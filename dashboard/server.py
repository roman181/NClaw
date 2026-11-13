"""Local-only HTTP server for the NClaw dashboard.

Serves the dashboard and a strict local API allowlist. Agent actions require
explicit one-time approval; inference is a separate explicit local Ollama call.
There is no shell, dynamic code, or arbitrary file-management API.
"""
from __future__ import annotations

import ipaddress
import json
import os
import platform
import shutil
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from core.agent_runtime import AgentExecutionError, AgentRuntime
from core.approval_manager import ApprovalManager
from models.llama import LlamaModel
from models.ollama import OllamaClient, OllamaError
from tasks.store import STATUSES, TaskStore

HOST = "127.0.0.1"
PORT = int(os.getenv("NCLAW_DASHBOARD_PORT", "8765"))
WEB_ROOT = Path(__file__).resolve().parent / "static"
STORE = TaskStore()


def _validate_task_payload(payload: dict[str, object]) -> tuple[str, str, int]:
    allowed = {"title", "description", "priority"}
    if set(payload) - allowed:
        raise ValueError("Unknown task action fields")
    title = payload.get("title")
    description = payload.get("description", "")
    priority = payload.get("priority", 3)
    if not isinstance(title, str) or not title.strip() or len(title) > 200:
        raise ValueError("Task title must contain 1 to 200 characters")
    if not isinstance(description, str) or len(description) > 5000:
        raise ValueError("Task description must not exceed 5000 characters")
    if type(priority) is not int or not 1 <= priority <= 5:
        raise ValueError("Task priority must be an integer from 1 to 5")
    return title.strip(), description, priority


def _create_task_action(payload: dict[str, object]) -> dict[str, object]:
    """The sole dashboard agent action: create one validated local task."""
    title, description, priority = _validate_task_payload(payload)
    return STORE.create(title, description, priority)


RUNTIME = AgentRuntime(ApprovalManager(db_path=STORE.path.parent / "approvals.sqlite3"))
RUNTIME.register("task-assistant", _create_task_action)


def _approval_json(record) -> dict[str, object]:
    item: dict[str, object] = {
        "request_id": record.request_id,
        "action": record.action,
        "description": record.description,
        "status": record.status,
        "created_at": record.created_at,
        "expires_at": record.expires_at,
    }
    if record.status in {"pending", "approved"}:
        try:
            item["payload"] = RUNTIME.payload_for(record.request_id)
        except KeyError:
            pass
    return item


def _execution_json(record) -> dict[str, object]:
    if isinstance(record, dict):
        return record
    return {
        "execution_id": record.execution_id,
        "agent": record.agent,
        "approval_id": record.approval_id,
        "status": record.status,
        "created_at": record.created_at,
        "finished_at": record.finished_at,
        "error": record.error,
    }


def run_model_inference(model: str, prompt: str) -> str:
    """Run one explicit inference using an installed local Ollama model."""
    if not isinstance(model, str) or not model.strip() or len(model) > 120:
        raise ValueError("A valid installed model name is required")
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 16_000:
        raise ValueError("Prompt must contain 1 to 16000 characters")
    inventory = ollama_models()
    installed = {
        item["name"] for item in inventory.get("models", [])
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    if not inventory.get("available") or model not in installed:
        raise ValueError("Selected model is not available in the local Ollama inventory")
    return LlamaModel(client=OllamaClient(timeout=60), model=model).generate(prompt)


class _NoRedirect(HTTPRedirectHandler):
    """Do not allow a configured local endpoint to redirect requests elsewhere."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def ollama_status() -> dict[str, object]:
    """Check the explicitly configured private Ollama host; never run models."""
    configured_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").strip()
    try:
        parsed = urlsplit(configured_host)
        hostname = parsed.hostname
        if (
            parsed.scheme not in {"http", "https"}
            or not hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise ValueError("Invalid Ollama URL")
        try:
            address = ipaddress.ip_address(hostname)
            allowed_host = address.is_private or address.is_loopback
        except ValueError:
            allowed_host = hostname.lower().endswith(".local")
        if not allowed_host:
            raise ValueError("Ollama host must be a private LAN or loopback address")
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        if not 1 <= port <= 65535:
            raise ValueError("Invalid Ollama port")
        base_url = urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
        endpoint = f"{hostname}:{port}"
    except ValueError:
        return {
            "ok": True,
            "available": False,
            "version": None,
            "endpoint": "Ungültige OLLAMA_HOST-Konfiguration",
        }

    request = Request(
        f"{base_url}/api/version",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        opener = build_opener(_NoRedirect())
        with opener.open(request, timeout=0.8) as response:
            payload = json.loads(response.read(4096))
        version = payload.get("version") if isinstance(payload, dict) else None
        return {
            "ok": True,
            "available": isinstance(version, str) and bool(version),
            "version": version if isinstance(version, str) else None,
            "endpoint": endpoint,
        }
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        return {
            "ok": True,
            "available": False,
            "version": None,
            "endpoint": endpoint,
        }


def ollama_models() -> dict[str, object]:
    """List locally available Ollama model metadata; never loads or runs a model."""
    status = ollama_status()
    if not status.get("available"):
        return {"ok": True, "available": False, "models": [], "endpoint": status.get("endpoint")}
    configured_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").strip()
    parsed = urlsplit(configured_host)
    base_url = urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
    request = Request(
        f"{base_url}/api/tags",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        opener = build_opener(_NoRedirect())
        with opener.open(request, timeout=1.0) as response:
            payload = json.loads(response.read(32_768))
        raw_models = payload.get("models", []) if isinstance(payload, dict) else []
        models = []
        if isinstance(raw_models, list):
            for item in raw_models[:50]:
                if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                    continue
                models.append({
                    "name": item["name"][:160],
                    "size": item.get("size") if isinstance(item.get("size"), int) else None,
                    "modified_at": item.get("modified_at") if isinstance(item.get("modified_at"), str) else None,
                })
        return {"ok": True, "available": True, "models": models, "endpoint": status.get("endpoint")}
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        return {"ok": True, "available": True, "models": [], "error": "Modellliste momentan nicht lesbar", "endpoint": status.get("endpoint")}


def system_metrics() -> dict[str, object]:
    """Return best-effort, read-only host metrics without optional dependencies."""
    memory = None
    meminfo = Path("/proc/meminfo")
    if meminfo.is_file():
        values = {}
        for line in meminfo.read_text(encoding="ascii", errors="ignore").splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0].rstrip(":") in {"MemTotal", "MemAvailable"}:
                values[parts[0].rstrip(":")] = int(parts[1]) * 1024
        total, available = values.get("MemTotal"), values.get("MemAvailable")
        if total and available is not None:
            memory = {"total_bytes": total, "available_bytes": available, "used_percent": round((total - available) / total * 100, 1)}
    disk = shutil.disk_usage(Path.home())
    try:
        load = list(os.getloadavg())
    except (AttributeError, OSError):
        load = None
    uptime = None
    uptime_file = Path("/proc/uptime")
    if uptime_file.is_file():
        try:
            uptime = int(float(uptime_file.read_text(encoding="ascii").split()[0]))
        except (ValueError, OSError, IndexError):
            pass
    return {"ok": True, "platform": platform.system() or "Unknown", "release": platform.release(), "python": platform.python_version(), "memory": memory, "disk": {"total_bytes": disk.total, "free_bytes": disk.free, "used_percent": round((disk.total - disk.free) / disk.total * 100, 1) if disk.total else 0}, "load_average": load, "uptime_seconds": uptime}

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
            raise TypeError("JSON object required")
        return value

    def do_GET(self) -> None:
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
        if path == "/api/system":
            self._json(200, system_metrics())
            return
        if path == "/api/agent-status":
            self._json(200, ollama_status())
            return
        if path == "/api/agent-models":
            self._json(200, ollama_models())
            return
        if path == "/api/approvals":
            self._json(200, {"approvals": [
                _approval_json(record) for record in RUNTIME.approvals.list(limit=50)
            ]})
            return
        if path == "/api/agent-executions":
            records = RUNTIME.approvals.list_executions(limit=50)
            self._json(200, {"executions": [_execution_json(record) for record in records]})
            return
        if path == "/api/tasks":
            self._json(200, {"tasks": STORE.list(limit=200)})
            return
        if path == "/api/backups":
            backup_dir = STORE.path.parent / "backups"
            backups = []
            if backup_dir.is_dir() and not backup_dir.is_symlink():
                for item in backup_dir.iterdir():
                    if item.name.startswith("tasks-") and item.name.endswith(".sqlite3") and not item.is_symlink() and item.is_file():
                        info = item.stat()
                        backups.append({
                            "filename": item.name,
                            "size": info.st_size,
                            "modified_at": datetime.fromtimestamp(info.st_mtime, timezone.utc).isoformat(),  # noqa: UP017 - keep Python 3.10 compatibility
                        })
            backups.sort(key=lambda item: item["modified_at"], reverse=True)
            self._json(200, {"backups": backups[:20]})
            return
        prefix, suffix = "/api/tasks/", "/history"
        if path.startswith(prefix) and path.endswith(suffix):
            task_id = path[len(prefix):-len(suffix)]
            try:
                self._json(200, {"events": STORE.history(task_id)})
            except KeyError as exc:
                self._json(404, {"error": str(exc)})
            return
        files = {
            "/": "index.html",
            "/index.html": "index.html",
            "/style.css": "style.css",
            "/app.js": "app.js",
            "/manifest.webmanifest": "manifest.webmanifest",
            "/sw.js": "sw.js",
            "/icon.svg": "icon.svg",
        }
        filename = files.get(path)
        if filename is None:
            self._json(404, {"error": "Route not found"})
            return
        content = (WEB_ROOT / filename).read_bytes()
        content_type = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".webmanifest": "application/manifest+json; charset=utf-8",
            ".svg": "image/svg+xml",
        }[Path(filename).suffix]
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; font-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self' data:")
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        if self.client_address[0] not in {"127.0.0.1", "::1"}:
            self._json(403, {"error": "Local access only"})
            return
        path = urlparse(self.path).path
        try:
            payload = self._body()
            if path == "/api/agent-actions/propose":
                agent = payload.get("agent")
                action_payload = payload.get("payload")
                if agent != "task-assistant" or not isinstance(action_payload, dict):
                    raise ValueError("Only the registered task-assistant action is available")
                _validate_task_payload(action_payload)
                approval = RUNTIME.propose(agent, action_payload)
                self._json(201, {"approval": _approval_json(approval)})
                return
            if path.startswith("/api/approvals/") and path.endswith("/decision"):
                request_id = path[len("/api/approvals/"):-len("/decision")].strip("/")
                decision = payload.get("decision")
                if not request_id or decision not in {"approve", "reject"}:
                    raise ValueError("A valid approval ID and decision are required")
                record = (
                    RUNTIME.approvals.approve(request_id)
                    if decision == "approve"
                    else RUNTIME.approvals.reject(request_id)
                )
                self._json(200, {"approval": _approval_json(record)})
                return
            if path == "/api/agent-executions":
                approval_id = payload.get("approval_id")
                agent = payload.get("agent")
                if not isinstance(approval_id, str) or agent != "task-assistant":
                    raise ValueError("Approval ID and registered agent are required")
                record, result = RUNTIME.execute(approval_id, agent)
                self._json(200, {"execution": _execution_json(record), "result": result})
                return
            if path == "/api/inference":
                model, prompt = payload.get("model"), payload.get("prompt")
                answer = run_model_inference(model, prompt)
                self._json(200, {"ok": True, "model": model, "answer": answer})
                return
            if path == "/api/backup":
                backup_dir = STORE.path.parent / "backups"
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")  # noqa: UP017 - keep Python 3.10 compatibility
                backup_path = STORE.backup(backup_dir / f"tasks-{stamp}.sqlite3")
                self._json(201, {"ok": True, "filename": backup_path.name})
                return
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
        except PermissionError as exc:
            self._json(403, {"error": str(exc)})
        except TimeoutError as exc:
            self._json(410, {"error": str(exc)})
        except AgentExecutionError as exc:
            self._json(422, {"error": str(exc)})
        except OllamaError as exc:
            self._json(502, {"error": str(exc)})
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})

    def do_OPTIONS(self) -> None:
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
