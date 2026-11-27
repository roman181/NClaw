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


def test_sqlite_concurrent_decisions_are_atomic_across_manager_instances(
    tmp_path, monkeypatch
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    database = tmp_path / "approvals.sqlite3"
    creator = ApprovalManager(db_path=database)
    request = creator.create("agent.run:notes", "Run a notes agent")

    approver = ApprovalManager(db_path=database)
    rejecter = ApprovalManager(db_path=database)
    pending_reads = Barrier(2)

    def synchronize_pending_reads(manager):
        original_get = manager._get

        def synchronized_get(request_id):
            record = original_get(request_id)
            if record.status == "pending":
                pending_reads.wait(timeout=5)
            return record

        monkeypatch.setattr(manager, "_get", synchronized_get)

    synchronize_pending_reads(approver)
    synchronize_pending_reads(rejecter)

    def decide(manager, method_name):
        try:
            result = getattr(manager, method_name)(request.request_id)
            return ("success", result.status)
        except ValueError:
            return ("conflict", None)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(decide, approver, "approve"),
            executor.submit(decide, rejecter, "reject"),
        ]
        results = [future.result(timeout=10) for future in futures]

    assert sum(result[0] == "success" for result in results) == 1
    assert sum(result[0] == "conflict" for result in results) == 1
    final_status = creator.get(request.request_id).status
    assert final_status in {"approved", "rejected"}
    assert final_status == next(result[1] for result in results if result[0] == "success")



def test_sqlite_concurrent_consumption_is_one_time_across_manager_instances(
    tmp_path, monkeypatch
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    database = tmp_path / "approvals.sqlite3"
    creator = ApprovalManager(db_path=database)
    request = creator.create(
        "agent.run:notes", "Run a notes agent", binding="payload-digest"
    )
    creator.approve(request.request_id)

    consumers = [
        ApprovalManager(db_path=database),
        ApprovalManager(db_path=database),
    ]
    approved_reads = Barrier(2)

    for manager in consumers:
        original_get = manager._get
        synchronized = {"first": True}

        def synchronized_get(request_id, *, _get=original_get, _state=synchronized):
            record = _get(request_id)
            if record.status == "approved" and _state["first"]:
                _state["first"] = False
                approved_reads.wait(timeout=5)
            return record

        monkeypatch.setattr(manager, "_get", synchronized_get)

    def consume(manager):
        try:
            record = manager.consume(
                request.request_id, "agent.run:notes", "payload-digest"
            )
            return ("success", record.status)
        except PermissionError:
            return ("denied", None)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(consume, manager) for manager in consumers]
        results = [future.result(timeout=10) for future in futures]

    assert sum(result[0] == "success" for result in results) == 1
    assert sum(result[0] == "denied" for result in results) == 1
    assert creator.get(request.request_id).status == "consumed"


@pytest.mark.parametrize("persistent", [False, True])
def test_approval_payload_is_bounded_before_storage(tmp_path, persistent):
    database = tmp_path / "approvals.sqlite3" if persistent else None
    manager = ApprovalManager(db_path=database)

    with pytest.raises(ValueError, match="16 KiB"):
        manager.create(
            "agent.run:notes",
            "Run a notes agent",
            payload={"text": "x" * (16 * 1024)},
        )
    assert manager.list() == []

    with pytest.raises(TypeError, match="JSON object"):
        manager.create(
            "agent.run:notes",
            "Run a notes agent",
            payload=["not", "an", "object"],
        )
    assert manager.list() == []


def test_approval_payload_limit_counts_utf8_bytes():
    manager = ApprovalManager()
    with pytest.raises(ValueError, match="16 KiB"):
        manager.create(
            "agent.run:notes",
            "Run a notes agent",
            payload={"text": "ä" * 9_000},
        )


def test_approval_payload_is_copied_before_storage():
    manager = ApprovalManager()
    original = {"nested": {"value": "before"}}
    request = manager.create(
        "agent.run:notes",
        "Run a notes agent",
        payload=original,
    )

    original["nested"]["value"] = "after"

    assert manager.payload_for(request.request_id) == {
        "nested": {"value": "before"}
    }



def test_running_execution_reports_process_state_without_exposing_pid(tmp_path):
    from types import SimpleNamespace

    from core.process_identity import current_process_identity

    pid, start_token = current_process_identity()
    manager = ApprovalManager(db_path=tmp_path / "approvals.sqlite3")
    manager.save_execution(SimpleNamespace(
        execution_id="exec-running",
        agent="notes",
        approval_id="approval-running",
        status="running",
        created_at=100.0,
        finished_at=None,
        error=None,
        owner_pid=pid,
        owner_start_token=start_token,
    ))

    record = manager.list_executions()[0]
    assert record["process_state"] == ("active" if start_token else "unknown")
    assert "owner_pid" not in record
    assert "owner_start_token" not in record


def test_legacy_execution_schema_migrates_without_losing_running_rows(tmp_path):
    import sqlite3

    database = tmp_path / "legacy-approvals.sqlite3"
    with sqlite3.connect(database) as db:
        db.execute(
            """CREATE TABLE agent_executions (
                execution_id TEXT PRIMARY KEY, agent TEXT NOT NULL,
                approval_id TEXT NOT NULL, status TEXT NOT NULL,
                created_at REAL NOT NULL, finished_at REAL, error TEXT
            )"""
        )
        db.execute(
            "INSERT INTO agent_executions VALUES(?,?,?,?,?,?,?)",
            ("legacy-running", "notes", "approval-old", "running", 100.0, None, None),
        )

    manager = ApprovalManager(db_path=database)
    records = manager.list_executions()
    assert records[0]["execution_id"] == "legacy-running"
    assert records[0]["status"] == "running"
    assert records[0]["process_state"] == "unknown"

@pytest.mark.parametrize("limit", [0, -1, 201, True, 1.5, "10"])
def test_execution_history_limit_is_bounded(tmp_path, limit):
    manager = ApprovalManager(db_path=tmp_path / "approvals.sqlite3")
    with pytest.raises(ValueError, match="between 1 and 200"):
        manager.list_executions(limit)


def test_execution_history_accepts_maximum_limit(tmp_path):
    manager = ApprovalManager(db_path=tmp_path / "approvals.sqlite3")
    assert manager.list_executions(200) == []

