"""Persistent, local-only task tracking for NClaw.

The task store records plans and progress. It deliberately does not execute tasks,
shell commands, network requests, or external side effects.
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

STATUSES = {"queued", "in_progress", "blocked", "completed", "failed", "cancelled"}
TRANSITIONS = {
    "queued": {"in_progress", "blocked", "cancelled"},
    "in_progress": {"blocked", "completed", "failed", "cancelled", "queued"},
    "blocked": {"queued", "cancelled"},
    "failed": {"queued", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class TaskStore:
    """SQLite task ledger stored on the local device with restrictive permissions."""

    def __init__(self, path: str | Path | None = None) -> None:
        configured = path or Path(os.getenv("NCLAW_DATA_DIR", "~/.nclaw")).expanduser() / "tasks.sqlite3"
        self.path = Path(configured).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            self.path.parent.chmod(0o700)
        except OSError:
            pass
        self._initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL CHECK(status IN
                        ('queued','in_progress','blocked','completed','failed','cancelled')),
                    priority INTEGER NOT NULL CHECK(priority BETWEEN 1 AND 5),
                    due_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS task_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL REFERENCES tasks(id),
                    old_status TEXT,
                    new_status TEXT NOT NULL,
                    note TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )
            db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status_priority ON tasks(status, priority, created_at)")

        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    def create(
        self,
        title: str,
        description: str = "",
        priority: int = 3,
        due_at: str | None = None,
    ) -> dict[str, object]:
        title = title.strip()
        if not title or len(title) > 200:
            raise ValueError("Title must contain 1–200 characters")
        if len(description) > 20_000:
            raise ValueError("Description is too long")
        if isinstance(priority, bool) or not 1 <= priority <= 5:
            raise ValueError("Priority must be an integer from 1 (highest) to 5")
        task_id, now = uuid.uuid4().hex, _now()
        with self._connect() as db:
            db.execute(
                """INSERT INTO tasks
                   (id,title,description,status,priority,due_at,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (task_id, title, description, "queued", priority, due_at, now, now),
            )
            db.execute(
                "INSERT INTO task_events(task_id,old_status,new_status,note,created_at) VALUES(?,?,?,?,?)",
                (task_id, None, "queued", "Task created", now),
            )
        return self.get(task_id)

    def get(self, task_id: str) -> dict[str, object]:
        with self._connect() as db:
            row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise KeyError(f"Unknown task: {task_id}")
        return dict(row)

    def list(self, status: str | None = None, limit: int = 100) -> list[dict[str, object]]:
        if status is not None and status not in STATUSES:
            raise ValueError("Unknown task status")
        if isinstance(limit, bool) or not 1 <= limit <= 500:
            raise ValueError("Limit must be between 1 and 500")
        with self._connect() as db:
            if status:
                rows = db.execute(
                    "SELECT * FROM tasks WHERE status = ? ORDER BY priority ASC, created_at ASC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = db.execute(
                    "SELECT * FROM tasks ORDER BY priority ASC, created_at ASC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [dict(row) for row in rows]

    def transition(self, task_id: str, new_status: str, note: str = "") -> dict[str, object]:
        if new_status not in STATUSES:
            raise ValueError("Unknown task status")
        if len(note) > 2_000:
            raise ValueError("Event note is too long")
        now = _now()
        with self._connect() as db:
            row = db.execute("SELECT status FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if row is None:
                raise KeyError(f"Unknown task: {task_id}")
            old_status = str(row["status"])
            if new_status not in TRANSITIONS[old_status]:
                raise ValueError(f"Invalid task transition: {old_status} -> {new_status}")
            db.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                (new_status, now, task_id),
            )
            db.execute(
                """INSERT INTO task_events(task_id,old_status,new_status,note,created_at)
                   VALUES(?,?,?,?,?)""",
                (task_id, old_status, new_status, note, now),
            )
        return self.get(task_id)

    def history(self, task_id: str) -> list[dict[str, object]]:
        with self._connect() as db:
            exists = db.execute("SELECT 1 FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if exists is None:
                raise KeyError(f"Unknown task: {task_id}")
            rows = db.execute(
                "SELECT old_status,new_status,note,created_at FROM task_events WHERE task_id = ? ORDER BY event_id",
                (task_id,),
            ).fetchall()
        return [dict(row) for row in rows]
