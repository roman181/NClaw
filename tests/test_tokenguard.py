"""Tests for context threshold checks and private local handoff files."""
import json

import pytest

from tokenguard.handoff import HandoffStore
from tokenguard.monitor import TokenGuard


def test_token_guard_triggers_at_ninety_percent():
    guard = TokenGuard(context_window=1000, threshold=0.9)
    check = guard.check("x" * 3600)
    assert check.estimated_tokens >= 900
    assert check.should_handoff


def test_token_guard_does_not_trigger_below_threshold():
    guard = TokenGuard(context_window=1000, threshold=0.9)
    check = guard.check("short task")
    assert not check.should_handoff


def test_token_guard_rejects_invalid_configuration():
    with pytest.raises(ValueError):
        TokenGuard(context_window=100, threshold=0.9)
    with pytest.raises(ValueError):
        TokenGuard(context_window=4096, threshold=0.05)


def test_handoff_is_private_json_inside_metadata(tmp_path):
    store = HandoffStore(tmp_path / "nclaw")
    path = store.create(
        goal="Analyze this repository",
        model="llama3.2",
        estimated_tokens=920,
        context_window=1000,
        usage_ratio=0.92,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["goal"] == "Analyze this repository"
    assert payload["status"] == "waiting_for_manual_resume"
    assert path.parent == tmp_path / "nclaw" / "metadata" / "handoffs"
    assert path.stat().st_mode & 0o077 == 0


def test_handoff_rejects_symlinked_metadata(tmp_path):
    root = tmp_path / "nclaw"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "metadata").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="metadata"):
        HandoffStore(root).create(
            goal="task", model="llama3.2", estimated_tokens=10,
            context_window=1000, usage_ratio=0.01,
        )
