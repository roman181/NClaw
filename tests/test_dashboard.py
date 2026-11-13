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
