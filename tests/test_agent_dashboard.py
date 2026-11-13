"""Integration tests for approval-gated dashboard actions and inference."""
from __future__ import annotations

import json
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import dashboard.server as dashboard_server
from core.agent_runtime import AgentRuntime
from tasks.store import TaskStore


def _start_dashboard(monkeypatch, tmp_path):
    store = TaskStore(tmp_path / "tasks.sqlite3")
    monkeypatch.setattr(dashboard_server, "STORE", store)
    runtime = AgentRuntime()
    runtime.register("task-assistant", dashboard_server._create_task_action)
    monkeypatch.setattr(dashboard_server, "RUNTIME", runtime)
    server = ThreadingHTTPServer(("127.0.0.1", 0), dashboard_server.DashboardHandler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    return store, server, worker, f"http://127.0.0.1:{server.server_port}"


def _post(base, path, payload):
    request = Request(
        base + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return urlopen(request, timeout=3)


def test_dashboard_agent_action_requires_separate_approval_and_execution(
    tmp_path, monkeypatch
):
    store, server, worker, base = _start_dashboard(monkeypatch, tmp_path)
    try:
        with _post(base, "/api/agent-actions/propose", {
            "agent": "task-assistant",
            "payload": {"title": "Approved task", "description": "Only after approval", "priority": 2},
        }) as response:
            proposed = json.loads(response.read())
            assert response.status == 201
        approval_id = proposed["approval"]["request_id"]
        assert proposed["approval"]["status"] == "pending"
        assert store.list() == []

        with urlopen(base + "/api/approvals", timeout=3) as response:
            approvals = json.loads(response.read())["approvals"]
            assert approvals[0]["payload"]["title"] == "Approved task"

        try:
            _post(base, "/api/agent-executions", {
                "approval_id": approval_id, "agent": "task-assistant",
            })
            raise AssertionError("An unapproved action must not execute")
        except HTTPError as error:
            assert error.code == 403
        assert store.list() == []

        with _post(base, f"/api/approvals/{approval_id}/decision", {"decision": "approve"}) as response:
            approved = json.loads(response.read())
            assert response.status == 200
            assert approved["approval"]["status"] == "approved"

        with _post(base, "/api/agent-executions", {
            "approval_id": approval_id, "agent": "task-assistant",
        }) as response:
            result = json.loads(response.read())
            assert response.status == 200
            assert result["execution"]["status"] == "completed"
            assert result["result"]["title"] == "Approved task"
        assert len(store.list()) == 1

        try:
            _post(base, "/api/agent-executions", {
                "approval_id": approval_id, "agent": "task-assistant",
            })
            raise AssertionError("An approval must be single-use")
        except HTTPError as error:
            assert error.code == 403
        assert len(store.list()) == 1

        with urlopen(base + "/api/agent-executions", timeout=3) as response:
            executions = json.loads(response.read())["executions"]
            assert executions[0]["status"] == "completed"
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)


def test_rejected_agent_action_never_creates_task(tmp_path, monkeypatch):
    store, server, worker, base = _start_dashboard(monkeypatch, tmp_path)
    try:
        with _post(base, "/api/agent-actions/propose", {
            "agent": "task-assistant", "payload": {"title": "Do not create"},
        }) as response:
            approval_id = json.loads(response.read())["approval"]["request_id"]
        with _post(base, f"/api/approvals/{approval_id}/decision", {"decision": "reject"}):
            pass
        try:
            _post(base, "/api/agent-executions", {
                "approval_id": approval_id, "agent": "task-assistant",
            })
            raise AssertionError("Rejected action must not execute")
        except HTTPError as error:
            assert error.code == 403
        assert store.list() == []
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)


def test_dashboard_rejects_unregistered_agent_and_invalid_payload(tmp_path, monkeypatch):
    store, server, worker, base = _start_dashboard(monkeypatch, tmp_path)
    try:
        for payload in (
            {"agent": "shell", "payload": {"command": "echo unsafe"}},
            {"agent": "task-assistant", "payload": {"title": "bad", "unexpected": True}},
            {"agent": "task-assistant", "payload": {"title": "bad", "priority": True}},
        ):
            try:
                _post(base, "/api/agent-actions/propose", payload)
                raise AssertionError("Invalid or unregistered action must be rejected")
            except HTTPError as error:
                assert error.code == 400
        assert store.list() == []
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)


def test_dashboard_inference_is_a_separate_explicit_route(tmp_path, monkeypatch):
    _store, server, worker, base = _start_dashboard(monkeypatch, tmp_path)
    calls = []
    monkeypatch.setattr(
        dashboard_server, "run_model_inference",
        lambda model, prompt: calls.append((model, prompt)) or "Lokale Antwort",
    )
    try:
        with _post(base, "/api/inference", {
            "model": "llama3.2:latest", "prompt": "Sag Hallo",
        }) as response:
            result = json.loads(response.read())
            assert response.status == 200
            assert result == {
                "ok": True, "model": "llama3.2:latest", "answer": "Lokale Antwort",
            }
        assert calls == [("llama3.2:latest", "Sag Hallo")]
        assert _store.list() == []
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)


def test_dashboard_page_exposes_distinct_approval_and_inference_controls(tmp_path, monkeypatch):
    _store, server, worker, base = _start_dashboard(monkeypatch, tmp_path)
    try:
        with urlopen(base + "/", timeout=3) as response:
            page = response.read().decode()
            assert 'id="agent-action-form"' in page
            assert 'id="approval-list"' in page
            assert 'id="execution-list"' in page
            assert 'id="inference-form"' in page
            assert "keine Agentenaktion" in page
        with urlopen(base + "/app.js", timeout=3) as response:
            script = response.read().decode()
            assert 'api("/api/agent-actions/propose"' in script
            assert 'api("/api/approvals/"+encodeURIComponent' in script
            assert 'api("/api/agent-executions"' in script
            assert 'api("/api/inference"' in script
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)
