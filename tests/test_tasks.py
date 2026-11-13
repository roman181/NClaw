from pathlib import Path

import pytest

from tasks.store import TaskStore


def test_create_and_persist_task(tmp_path: Path):
    db = tmp_path / "private" / "tasks.sqlite3"
    first = TaskStore(db)
    task = first.create("Build dashboard", "Create a read-only status view", priority=2)
    assert task["status"] == "queued"
    assert task["priority"] == 2
    assert TaskStore(db).get(str(task["id"]))["title"] == "Build dashboard"


def test_task_status_transitions_and_history(tmp_path: Path):
    store = TaskStore(tmp_path / "tasks.sqlite3")
    task = store.create("Review imports")
    task_id = str(task["id"])
    store.transition(task_id, "in_progress", "Started review")
    store.transition(task_id, "completed", "Checks passed")
    assert store.get(task_id)["status"] == "completed"
    assert [event["new_status"] for event in store.history(task_id)] == [
        "queued", "in_progress", "completed"
    ]


def test_terminal_task_cannot_be_reopened(tmp_path: Path):
    store = TaskStore(tmp_path / "tasks.sqlite3")
    task = store.create("One-time task")
    task_id = str(task["id"])
    store.transition(task_id, "cancelled")
    with pytest.raises(ValueError):
        store.transition(task_id, "queued")


def test_rejects_invalid_input(tmp_path: Path):
    store = TaskStore(tmp_path / "tasks.sqlite3")
    with pytest.raises(ValueError):
        store.create(" ")
    with pytest.raises(ValueError):
        store.create("Bad priority", priority=0)
    with pytest.raises(ValueError):
        store.list(status="unknown")


def test_priority_order_and_status_filter(tmp_path: Path):
    store = TaskStore(tmp_path / "tasks.sqlite3")
    store.create("Low priority", priority=5)
    urgent = store.create("Urgent", priority=1)
    assert store.list()[0]["id"] == urgent["id"]
    assert len(store.list(status="queued")) == 2
