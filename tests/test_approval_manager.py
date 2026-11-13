"""Tests for expiring one-time approval records."""
import pytest

from core.approval_manager import ApprovalManager


def test_request_starts_pending_and_can_be_approved() -> None:
    manager = ApprovalManager()
    request = manager.create("publish", "Publish release v0.1")
    assert request.status == "pending"
    assert manager.approve(request.request_id).status == "approved"


def test_rejected_request_cannot_be_consumed() -> None:
    manager = ApprovalManager()
    request = manager.create("delete", "Delete temporary file")
    manager.reject(request.request_id)
    with pytest.raises(PermissionError):
        manager.consume(request.request_id, "delete")


def test_approved_request_is_one_time_and_action_bound() -> None:
    manager = ApprovalManager()
    request = manager.create("publish", "Publish release")
    manager.approve(request.request_id)
    with pytest.raises(PermissionError):
        manager.consume(request.request_id, "delete")
    assert manager.consume(request.request_id, "publish").status == "consumed"
    with pytest.raises(PermissionError):
        manager.consume(request.request_id, "publish")


def test_approval_is_bound_to_exact_payload() -> None:
    manager = ApprovalManager()
    request = manager.create("file.create", "Create notes.txt", binding="digest-a")
    manager.approve(request.request_id)
    with pytest.raises(PermissionError):
        manager.consume(request.request_id, "file.create", "digest-b")
    assert manager.consume(request.request_id, "file.create", "digest-a").status == "consumed"


def test_expired_request_cannot_be_approved() -> None:
    manager = ApprovalManager(ttl_seconds=1)
    request = manager.create("install", "Install package")
    request.expires_at = 0
    with pytest.raises(TimeoutError):
        manager.approve(request.request_id)


def test_list_returns_recent_records_and_marks_expired_requests():
    manager = ApprovalManager(ttl_seconds=1)
    first = manager.create("task.create", "Create a task")
    second = manager.create("task.create", "Create another task")
    second.expires_at = 0
    records = manager.list()
    assert [record.request_id for record in records] == [second.request_id, first.request_id]
    assert records[0].status == "expired"
    assert records[1].status == "pending"



def test_sqlite_approvals_and_payload_survive_manager_restart(tmp_path):
    database = tmp_path / "approvals.sqlite3"
    first = ApprovalManager(db_path=database)
    request = first.create("agent.run:notes", "Create a note", binding="digest",
                           payload={"title": "Persistent plan"})
    first.approve(request.request_id)

    restarted = ApprovalManager(db_path=database)
    restored = restarted.get(request.request_id)
    assert restored.status == "approved"
    assert restarted.payload_for(request.request_id) == {"title": "Persistent plan"}
    assert restarted.consume(request.request_id, "agent.run:notes", "digest").status == "consumed"
    with pytest.raises(PermissionError):
        first.consume(request.request_id, "agent.run:notes", "digest")


def test_sqlite_execution_history_survives_manager_restart(tmp_path):
    from types import SimpleNamespace

    database = tmp_path / "approvals.sqlite3"
    manager = ApprovalManager(db_path=database)
    manager.save_execution(SimpleNamespace(
        execution_id="exec-1", agent="notes", approval_id="approval-1",
        status="completed", created_at=100.0, finished_at=101.0, error=None,
    ))
    restored = ApprovalManager(db_path=database)
    records = restored.list_executions()
    assert records[0]["execution_id"] == "exec-1"
    assert records[0]["status"] == "completed"
