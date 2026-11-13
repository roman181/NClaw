"""Integration tests for the loopback dashboard API."""
from __future__ import annotations

import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import dashboard.server as dashboard_server
from tasks.store import TaskStore


def test_dashboard_serves_ui_and_local_task_api(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(dashboard_server, "STORE", TaskStore(tmp_path / "tasks.sqlite3"))
    server = ThreadingHTTPServer(("127.0.0.1", 0), dashboard_server.DashboardHandler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(base + "/", timeout=3) as response:
            assert response.status == 200
            assert b"NClaw" in response.read()

        payload = json.dumps({"title": "Dashboard testen", "priority": 2}).encode()
        request = Request(base + "/api/tasks", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=3) as response:
            created = json.loads(response.read())
            assert response.status == 201
            assert created["task"]["title"] == "Dashboard testen"

        with urlopen(base + "/manifest.webmanifest", timeout=3) as response:
            manifest = json.loads(response.read())
            assert response.status == 200
            assert response.headers["Content-Type"].startswith("application/manifest+json")
            assert manifest["display"] == "standalone"
            assert manifest["start_url"] == "/"

        with urlopen(base + "/sw.js", timeout=3) as response:
            service_worker = response.read().decode("utf-8")
            assert response.status == 200
            assert "addAll" in service_worker
            assert "/api/" in service_worker
            assert "APP_SHELL.includes(url.pathname)" in service_worker
            assert "Never cache API responses or arbitrary same-origin URLs" in service_worker

        with urlopen(base + "/icon.svg", timeout=3) as response:
            assert response.status == 200
            assert response.headers["Content-Type"].startswith("image/svg+xml")

        with urlopen(base + "/api/status", timeout=3) as response:
            status = json.loads(response.read())
            assert status["counts"]["queued"] == 1
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)


def test_dashboard_does_not_expose_arbitrary_command_route(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(dashboard_server, "STORE", TaskStore(tmp_path / "tasks.sqlite3"))
    server = ThreadingHTTPServer(("127.0.0.1", 0), dashboard_server.DashboardHandler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        request = Request(
            f"http://127.0.0.1:{server.server_port}/api/execute",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(request, timeout=3)
            raise AssertionError("Arbitrary command route must not exist")
        except HTTPError as error:
            assert error.code == 404
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)


def test_task_history_endpoint_returns_auditable_status_events(tmp_path: Path, monkeypatch):
    store = TaskStore(tmp_path / "tasks.sqlite3")
    task = store.create("Historie prüfen", priority=2)
    store.transition(task["id"], "in_progress", "Arbeit begonnen")
    monkeypatch.setattr(dashboard_server, "STORE", store)
    server = ThreadingHTTPServer(("127.0.0.1", 0), dashboard_server.DashboardHandler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/api/tasks/{task["id"]}/history"
        with urlopen(url, timeout=3) as response:
            payload = json.loads(response.read())
            assert response.status == 200
            assert [event["new_status"] for event in payload["events"]] == ["queued", "in_progress"]
            assert payload["events"][1]["note"] == "Arbeit begonnen"
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)


def test_task_history_endpoint_returns_404_for_unknown_task(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(dashboard_server, "STORE", TaskStore(tmp_path / "tasks.sqlite3"))
    server = ThreadingHTTPServer(("127.0.0.1", 0), dashboard_server.DashboardHandler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        try:
            urlopen(f"http://127.0.0.1:{server.server_port}/api/tasks/missing/history", timeout=3)
            raise AssertionError("Unknown task history must return 404")
        except HTTPError as error:
            assert error.code == 404
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)

def test_system_metrics_shape():
    metrics = dashboard_server.system_metrics()
    assert metrics["ok"] is True
    assert isinstance(metrics["platform"], str)
    assert 0 <= metrics["disk"]["used_percent"] <= 100
    assert metrics["memory"] is None or 0 <= metrics["memory"]["used_percent"] <= 100



def test_agent_status_endpoint_reports_local_service_state(monkeypatch):
    monkeypatch.setattr(
        dashboard_server,
        "ollama_status",
        lambda: {
            "ok": True,
            "available": False,
            "version": None,
            "endpoint": "127.0.0.1:11434",
        },
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), dashboard_server.DashboardHandler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/api/agent-status", timeout=3) as response:
            status = json.loads(response.read())
            assert response.status == 200
            assert status["ok"] is True
            assert status["available"] is False
            assert status["endpoint"] == "127.0.0.1:11434"
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)



def test_ollama_status_uses_explicit_private_lan_host(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self, size):
            assert size == 4096
            return b'{"version": "0.6.2"}'

    class Opener:
        def open(self, request, timeout):
            assert request.full_url == "http://192.168.1.50:11434/api/version"
            assert timeout == 0.8
            return Response()

    monkeypatch.setenv("OLLAMA_HOST", "http://192.168.1.50:11434")
    monkeypatch.setattr(dashboard_server, "build_opener", lambda *handlers: Opener())
    status = dashboard_server.ollama_status()
    assert status == {
        "ok": True,
        "available": True,
        "version": "0.6.2",
        "endpoint": "192.168.1.50:11434",
    }


def test_ollama_status_rejects_public_hosts(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "https://example.com:11434")
    status = dashboard_server.ollama_status()
    assert status["ok"] is True
    assert status["available"] is False
    assert status["version"] is None
    assert status["endpoint"] == "Ungültige OLLAMA_HOST-Konfiguration"

def test_ollama_status_does_not_follow_redirects(monkeypatch):
    calls = []
    handlers = []

    class Opener:
        def open(self, request, timeout):
            calls.append((request.full_url, timeout))
            raise HTTPError(
                request.full_url,
                302,
                "Found",
                {"Location": "https://example.com/api/version"},
                None,
            )

    def fake_build_opener(*configured_handlers):
        handlers.extend(configured_handlers)
        return Opener()

    monkeypatch.setenv("OLLAMA_HOST", "http://192.168.1.50:11434")
    monkeypatch.setattr(dashboard_server, "build_opener", fake_build_opener)

    status = dashboard_server.ollama_status()

    assert status["ok"] is True
    assert status["available"] is False
    assert status["version"] is None
    assert status["endpoint"] == "192.168.1.50:11434"
    assert calls == [("http://192.168.1.50:11434/api/version", 0.8)]
    assert len(handlers) == 1
    assert isinstance(handlers[0], dashboard_server._NoRedirect)
    assert handlers[0].redirect_request(None, None, 302, "Found", {}, "https://example.com/api/version") is None

