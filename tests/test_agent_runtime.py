"""Safety tests for approval-gated agent execution."""
import pytest

from core.agent_runtime import AgentExecutionError, AgentRuntime
from core.approval_manager import ApprovalManager


def test_agent_action_requires_matching_explicit_approval():
    runtime = AgentRuntime()
    calls = []
    runtime.register("notes", lambda payload: calls.append(payload) or {"ok": True})
    request = runtime.propose("notes", {"title": "Plan"})
    with pytest.raises(PermissionError):
        runtime.execute(request.request_id, "notes", {"title": "Plan"})
    assert calls == []


def test_agent_executes_once_after_approval_and_records_result():
    runtime = AgentRuntime()
    runtime.register("notes", lambda payload: {"saved": payload["title"]})
    payload = {"title": "Plan"}
    request = runtime.propose("notes", payload)
    runtime.approvals.approve(request.request_id)
    record, result = runtime.execute(request.request_id, "notes", payload)
    assert record.status == "completed"
    assert record.finished_at is not None
    assert result == {"saved": "Plan"}
    with pytest.raises(PermissionError):
        runtime.execute(request.request_id, "notes", payload)


def test_agent_approval_is_bound_to_exact_payload_and_agent():
    runtime = AgentRuntime()
    calls = []
    runtime.register("alpha", lambda payload: calls.append(payload))
    runtime.register("beta", lambda payload: calls.append(payload))
    request = runtime.propose("alpha", {"value": 1})
    runtime.approvals.approve(request.request_id)
    with pytest.raises(PermissionError):
        runtime.execute(request.request_id, "alpha", {"value": 2})
    with pytest.raises(PermissionError):
        runtime.execute(request.request_id, "beta", {"value": 1})
    assert calls == []


def test_unknown_agent_cannot_be_proposed_or_executed():
    runtime = AgentRuntime()
    with pytest.raises(KeyError):
        runtime.propose("unregistered", {})
    with pytest.raises(KeyError):
        runtime.execute("unknown", "unregistered", {})


def test_payload_must_be_bounded_json():
    runtime = AgentRuntime()
    runtime.register("notes", lambda payload: payload)
    with pytest.raises(ValueError):
        runtime.propose("notes", {"bad": float("nan")})
    with pytest.raises(ValueError):
        runtime.propose("notes", {"large": "x" * 20_000})


def test_persistent_execution_start_is_recorded_before_handler_runs(tmp_path):
    approvals = ApprovalManager(db_path=tmp_path / "approvals.sqlite3")
    runtime = AgentRuntime(approvals)
    observed = {}

    def inspect_start(_payload):
        observed["executions"] = approvals.list_executions()
        observed["approval_status"] = approvals.get(request.request_id).status
        return {"ok": True}

    runtime.register("notes", inspect_start)
    request = runtime.propose("notes", {"title": "Plan"})
    approvals.approve(request.request_id)

    runtime.execute(request.request_id, "notes")

    assert observed["approval_status"] == "consumed"
    assert len(observed["executions"]) == 1
    assert observed["executions"][0]["approval_id"] == request.request_id
    assert observed["executions"][0]["status"] == "running"
    assert approvals.list_executions()[0]["status"] == "completed"


def test_execution_start_insert_failure_rolls_back_approval_consumption(
    tmp_path, monkeypatch
):
    import sqlite3
    from types import SimpleNamespace

    approvals = ApprovalManager(db_path=tmp_path / "approvals.sqlite3")
    approvals.save_execution(SimpleNamespace(
        execution_id="collision",
        agent="existing",
        approval_id="existing-approval",
        status="completed",
        created_at=1.0,
        finished_at=2.0,
        error=None,
    ))
    runtime = AgentRuntime(approvals)
    calls = []
    runtime.register("notes", lambda payload: calls.append(payload))
    request = runtime.propose("notes", {"title": "Plan"})
    approvals.approve(request.request_id)
    monkeypatch.setattr("core.agent_runtime.secrets.token_urlsafe", lambda _size: "collision")

    with pytest.raises(sqlite3.IntegrityError):
        runtime.execute(request.request_id, "notes")

    assert approvals.get(request.request_id).status == "approved"
    assert calls == []
    assert [item["execution_id"] for item in approvals.list_executions()] == ["collision"]


def test_failed_action_is_recorded_and_approval_is_consumed():
    runtime = AgentRuntime()
    def fail(_payload):
        raise RuntimeError("private detail")
    runtime.register("worker", fail)
    request = runtime.propose("worker", {})
    runtime.approvals.approve(request.request_id)
    with pytest.raises(AgentExecutionError, match="RuntimeError"):
        runtime.execute(request.request_id, "worker", {})
    record = next(iter(runtime.executions.values()))
    assert record.status == "failed"
    assert record.error == "RuntimeError"
    assert record.finished_at is not None
    with pytest.raises(PermissionError):
        runtime.execute(request.request_id, "worker", {})
