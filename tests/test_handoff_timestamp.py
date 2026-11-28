"""Regression tests for timezone-aware Nexus handoff timestamps."""
import json

import pytest

from tokenguard.handoff import HandoffStore


def test_handoff_load_rejects_timestamp_without_timezone(tmp_path):
    store = HandoffStore(tmp_path / "nclaw")
    path = store.create(
        goal="task",
        model="llama3.2",
        estimated_tokens=10,
        context_window=1000,
        usage_ratio=0.01,
    )
    handoff_id = path.stem.removeprefix("handoff-")
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["created_at"] = "2026-11-28T12:00:00"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="timestamp"):
        store.load(handoff_id)


@pytest.mark.parametrize(
    "timestamp",
    ["2026-11-28T12:00:00+00:00", "2026-11-28T13:00:00+01:00"],
)
def test_handoff_load_accepts_timezone_aware_timestamp(tmp_path, timestamp):
    store = HandoffStore(tmp_path / "nclaw")
    path = store.create(
        goal="task",
        model="llama3.2",
        estimated_tokens=10,
        context_window=1000,
        usage_ratio=0.01,
    )
    handoff_id = path.stem.removeprefix("handoff-")
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["created_at"] = timestamp
    path.write_text(json.dumps(payload), encoding="utf-8")

    assert store.load(handoff_id)["created_at"] == timestamp
