"""Safety tests for approval-gated agent execution."""
import pytest

from core.agent_runtime import AgentExecutionError, AgentRuntime


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
