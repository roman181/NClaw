"""Local-only HTTP server for the NClaw dashboard.

Only serves this dashboard and exposes a small allowlist of task APIs.
It intentionally has no shell, file-management, agent-execution or internet API.
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from tasks.store import STATUSES, TaskStore

HOST = "127.0.0.1"
PORT = int(os.getenv("NCLAW_DASHBOARD_PORT", "8765"))
WEB_ROOT = Path(__file__).resolve().parent / "static"
STORE = TaskStore()


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "NClawDashboard/1.0"

    def log_message(self, fmt: str, *args: object) -> None:
        # Avoid writing task titles or request bodies to logs.
        print(f"[NClaw Dashboard] {self.address_string()} {self.command} {self.path.split('?')[0]}")

    def _json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        if length < 1 or length > 24_000:
            raise ValueError("Request body missing or too large")
        value = json.loads(self.rfile.read(length))
        if not isinstance(value, dict):
            raise ValueError("JSON object required")
        return value

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/status":
            tasks = STORE.list(limit=200)
            self._json(200, {
                "ok": True,
                "runtime": "Python",
                "storage": "SQLite · lokal",
                "tasks": tasks,
                "counts": {status: sum(task["status"] == status for task in tasks) for status in STATUSES},
            })
            return
        if path == "/api/tasks":
            self._json(200, {"tasks": STORE.list(limit=200)})
            return
        files = {"/": "index.html", "/index.html": "index.html", "/style.css": "style.css", "/app.js": "app.js"}
        filename = files.get(path)
        if filename is None:
            self._json(404, {"error": "Route not found"})
            return
        content = (WEB_ROOT / filename).read_bytes()
        content_type = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8"}[Path(filename).suffix]
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'self'; connect-src 'self'; img-src 'self' data:")
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:  # noqa: N802
        if self.client_address[0] not in {"127.0.0.1", "::1"}:
            self._json(403, {"error": "Local access only"})
            return
        path = urlparse(self.path).path
        try:
            payload = self._body()
            if path == "/api/tasks":
                title = payload.get("title")
                description = payload.get("description", "")
                priority = payload.get("priority", 3)
                if not isinstance(title, str) or not isinstance(description, str) or not isinstance(priority, int):
                    raise ValueError("Invalid task fields")
                task = STORE.create(title, description, priority)
                self._json(201, {"task": task})
                return
            prefix, suffix = "/api/tasks/", "/status"
            if path.startswith(prefix) and path.endswith(suffix):
                task_id = path[len(prefix):-len(suffix)]
                status, note = payload.get("status"), payload.get("note", "")
                if not isinstance(status, str) or not isinstance(note, str):
                    raise ValueError("Invalid status fields")
                task = STORE.transition(task_id, status, note)
                self._json(200, {"task": task})
                return
            self._json(404, {"error": "Route not found"})
        except KeyError as exc:
            self._json(404, {"error": str(exc)})
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._json(405, {"error": "Method not allowed"})


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), DashboardHandler)
    print(f"NClaw Dashboard läuft lokal: http://{HOST}:{PORT}")
    print("Beenden mit STRG+C. Keine Shell- oder Agent-Ausführung über das Dashboard.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nNClaw Dashboard wird beendet.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
