"""Thread-safe one-time approvals with optional SQLite persistence."""
from __future__ import annotations

import json
import secrets
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ApprovalRecord:
    request_id: str
    action: str
    description: str
    status: str
    created_at: float
    expires_at: float
    binding: str | None = None
    payload: dict[str, Any] | None = None


class ApprovalManager:
    def __init__(self, ttl_seconds: int = 600, db_path: str | Path | None = None) -> None:
        if not isinstance(ttl_seconds, int) or isinstance(ttl_seconds, bool) or ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be a positive integer")
        self.ttl_seconds = ttl_seconds
        self.db_path = Path(db_path).expanduser() if db_path is not None else None
        self._records: dict[str, ApprovalRecord] = {}
        self._executions: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()
        if self.db_path is not None:
            if self.db_path.is_symlink():
                raise ValueError("Approval database must not be a symbolic link")
            self.db_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            try:
                self.db_path.parent.chmod(0o700)
            except OSError:
                pass
            with self._connect() as db:
                db.executescript("""
                    CREATE TABLE IF NOT EXISTS approvals (
                        request_id TEXT PRIMARY KEY, action TEXT NOT NULL,
                        description TEXT NOT NULL, status TEXT NOT NULL,
                        created_at REAL NOT NULL, expires_at REAL NOT NULL,
                        binding TEXT, payload_json TEXT
                    );
                    CREATE INDEX IF NOT EXISTS idx_approvals_created ON approvals(created_at);
                    CREATE TABLE IF NOT EXISTS agent_executions (
                        execution_id TEXT PRIMARY KEY, agent TEXT NOT NULL,
                        approval_id TEXT NOT NULL, status TEXT NOT NULL,
                        created_at REAL NOT NULL, finished_at REAL, error TEXT
                    );
                    CREATE INDEX IF NOT EXISTS idx_executions_created ON agent_executions(created_at);
                """)
            try:
                self.db_path.chmod(0o600)
            except OSError:
                pass

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.db_path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _record(row: sqlite3.Row) -> ApprovalRecord:
        raw = row["payload_json"]
        return ApprovalRecord(
            row["request_id"], row["action"], row["description"], row["status"],
            row["created_at"], row["expires_at"], row["binding"],
            json.loads(raw) if raw else None,
        )

    def create(self, action: str, description: str, binding: str | None = None,
               payload: dict[str, Any] | None = None) -> ApprovalRecord:
        if not isinstance(action, str) or not isinstance(description, str):
            raise TypeError("Action and description must be text")
        action, description = action.strip(), description.strip()
        if not action or not description:
            raise ValueError("Action and description are required")
        if binding is not None and (not isinstance(binding, str) or not binding):
            raise ValueError("Binding must be a non-empty string")
        payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True, allow_nan=False) if payload is not None else None
        now = time.time()
        with self._lock:
            request_id = secrets.token_urlsafe(9)
            record = ApprovalRecord(request_id, action[:100], description[:3500],
                                    "pending", now, now + self.ttl_seconds, binding, payload)
            if self.db_path is None:
                self._records[request_id] = record
            else:
                with self._connect() as db:
                    db.execute(
                        "INSERT INTO approvals VALUES(?,?,?,?,?,?,?,?)",
                        (record.request_id, record.action, record.description, record.status,
                         record.created_at, record.expires_at, record.binding, payload_json),
                    )
            return record

    def _get(self, request_id: str) -> ApprovalRecord:
        if self.db_path is None:
            record = self._records.get(request_id)
            if record is None:
                raise KeyError("Approval request not found")
            return record
        with self._connect() as db:
            row = db.execute("SELECT * FROM approvals WHERE request_id=?", (request_id,)).fetchone()
        if row is None:
            raise KeyError("Approval request not found")
        return self._record(row)

    def _decide(self, request_id: str, decision: str) -> ApprovalRecord:
        with self._lock:
            if self.db_path is None:
                record = self._get(request_id)
                if record.status != "pending":
                    raise ValueError(f"Request is already {record.status}")
                if time.time() >= record.expires_at:
                    self._set_status(request_id, "expired")
                    raise TimeoutError("Approval request expired")
                self._set_status(request_id, decision)
                return self._get(request_id)

            # Serialize decisions across processes, not just threads sharing this
            # manager instance. The conditional UPDATE makes pending -> decision
            # a single atomic state transition.
            failure: Exception | None = None
            with self._connect() as db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute(
                    "SELECT status, expires_at FROM approvals WHERE request_id=?",
                    (request_id,),
                ).fetchone()
                if row is None:
                    failure = KeyError("Approval request not found")
                elif row["status"] != "pending":
                    failure = ValueError(f"Request is already {row['status']}")
                else:
                    now = time.time()
                    if now >= row["expires_at"]:
                        db.execute(
                            "UPDATE approvals SET status='expired' "
                            "WHERE request_id=? AND status='pending'",
                            (request_id,),
                        )
                        failure = TimeoutError("Approval request expired")
                    else:
                        changed = db.execute(
                            "UPDATE approvals SET status=? "
                            "WHERE request_id=? AND status='pending' AND expires_at>?",
                            (decision, request_id, now),
                        ).rowcount
                        if changed != 1:
                            current = db.execute(
                                "SELECT status FROM approvals WHERE request_id=?",
                                (request_id,),
                            ).fetchone()
                            if current is None:
                                failure = KeyError("Approval request not found")
                            elif current["status"] != "pending":
                                failure = ValueError(
                                    f"Request is already {current['status']}"
                                )
                            else:
                                db.execute(
                                    "UPDATE approvals SET status='expired' "
                                    "WHERE request_id=? AND status='pending'",
                                    (request_id,),
                                )
                                failure = TimeoutError("Approval request expired")
            if failure is not None:
                raise failure
            return self._get(request_id)

    def _set_status(self, request_id: str, status: str) -> None:
        if self.db_path is None:
            self._records[request_id].status = status
        else:
            with self._connect() as db:
                db.execute("UPDATE approvals SET status=? WHERE request_id=?", (status, request_id))

    def approve(self, request_id: str) -> ApprovalRecord:
        return self._decide(request_id, "approved")

    def reject(self, request_id: str) -> ApprovalRecord:
        return self._decide(request_id, "rejected")

    def consume(self, request_id: str, expected_action: str,
                expected_binding: str | None = None) -> ApprovalRecord:
        with self._lock:
            record = self._get(request_id)
            if record.status != "approved":
                raise PermissionError("Request has not been approved")
            if time.time() >= record.expires_at:
                self._set_status(request_id, "expired")
                raise TimeoutError("Approval request expired")
            if record.action != expected_action:
                raise PermissionError("Approval does not match the requested action")
            if record.binding != expected_binding:
                raise PermissionError("Approval does not match the exact action payload")
            if self.db_path is None:
                self._set_status(request_id, "consumed")
            else:
                with self._connect() as db:
                    db.execute("BEGIN IMMEDIATE")
                    changed = db.execute(
                        "UPDATE approvals SET status='consumed' WHERE request_id=? AND status='approved' AND expires_at>?",
                        (request_id, time.time()),
                    ).rowcount
                    if changed != 1:
                        raise PermissionError("Approval was already consumed or expired")
            return self._get(request_id)

    def get(self, request_id: str) -> ApprovalRecord:
        with self._lock:
            record = self._get(request_id)
            if record.status in {"pending", "approved"} and time.time() >= record.expires_at:
                self._set_status(request_id, "expired")
                record.status = "expired"
            return record

    def payload_for(self, request_id: str) -> dict[str, Any]:
        record = self.get(request_id)
        if record.payload is None:
            raise KeyError("Approval payload is no longer available")
        return json.loads(json.dumps(record.payload, ensure_ascii=False))

    def pending(self) -> list[ApprovalRecord]:
        return [record for record in self.list() if record.status == "pending"]

    def list(self, limit: int = 50) -> list[ApprovalRecord]:
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        now = time.time()
        with self._lock:
            if self.db_path is None:
                for record in self._records.values():
                    if record.status in {"pending", "approved"} and now >= record.expires_at:
                        record.status = "expired"
                return sorted(self._records.values(), key=lambda r: r.created_at, reverse=True)[:limit]
            with self._connect() as db:
                db.execute("UPDATE approvals SET status='expired' WHERE status IN ('pending','approved') AND expires_at<=?", (now,))
                rows = db.execute("SELECT * FROM approvals ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [self._record(row) for row in rows]

    def save_execution(self, record: Any) -> None:
        item = {
            "execution_id": record.execution_id, "agent": record.agent,
            "approval_id": record.approval_id, "status": record.status,
            "created_at": record.created_at, "finished_at": record.finished_at,
            "error": record.error,
        }
        with self._lock:
            if self.db_path is None:
                self._executions[item["execution_id"]] = item
            else:
                with self._connect() as db:
                    db.execute("""INSERT OR REPLACE INTO agent_executions
                        VALUES(?,?,?,?,?,?,?)""", tuple(item.values()))

    def list_executions(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            if self.db_path is None:
                return sorted(self._executions.values(), key=lambda r: r["created_at"], reverse=True)[:limit]
            with self._connect() as db:
                rows = db.execute("SELECT * FROM agent_executions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(row) for row in rows]
