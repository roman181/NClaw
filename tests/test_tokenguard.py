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


@pytest.mark.parametrize("text", ["汉" * 100, "あ" * 100, "한" * 100])
def test_token_guard_conservatively_counts_cjk_without_spaces(text):
    assert TokenGuard.estimate_tokens(text) >= 150


def test_token_guard_counts_mixed_cjk_and_latin_text():
    mixed = "Analyze " + "漢字" * 50 + " repository"
    estimate = TokenGuard.estimate_tokens(mixed)
    assert estimate >= 150
    assert estimate > TokenGuard.estimate_tokens("Analyze repository")


@pytest.mark.parametrize("text", ["\ud800", "before\udfffafter", "\ud800\udfff"])
def test_token_guard_handles_unpaired_surrogates(text):
    estimate = TokenGuard.estimate_tokens(text)
    assert estimate >= 1


def test_token_guard_keeps_empty_text_at_zero():
    assert TokenGuard.estimate_tokens("") == 0


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


def test_handoff_load_validates_versioned_payload_without_resuming(tmp_path):
    store = HandoffStore(tmp_path / "nclaw")
    path = store.create(
        goal="Continue analysis", model="llama3.2", estimated_tokens=920,
        context_window=1000, usage_ratio=0.92,
    )
    handoff_id = path.stem.removeprefix("handoff-")
    payload = store.load(handoff_id)
    assert payload["goal"] == "Continue analysis"
    assert payload["status"] == "waiting_for_manual_resume"


@pytest.mark.parametrize("handoff_id", ["../outside", "not-a-uuid", ""])
def test_handoff_load_rejects_invalid_ids(tmp_path, handoff_id):
    with pytest.raises(ValueError, match="ID"):
        HandoffStore(tmp_path / "nclaw").load(handoff_id)


def test_handoff_load_rejects_unknown_schema_version(tmp_path):
    store = HandoffStore(tmp_path / "nclaw")
    path = store.create(
        goal="task", model="llama3.2", estimated_tokens=10,
        context_window=1000, usage_ratio=0.01,
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    data["schema_version"] = 2
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="schema"):
        store.load(data["handoff_id"])


def test_handoff_load_rejects_duplicate_json_keys(tmp_path):
    store = HandoffStore(tmp_path / "nclaw")
    path = store.create(
        goal="task", model="llama3.2", estimated_tokens=10,
        context_window=1000, usage_ratio=0.01,
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(
        json.dumps(data)[:-1] + ', "goal": "tampered"}', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="Malformed"):
        store.load(data["handoff_id"])


def test_handoff_load_rejects_oversized_file(tmp_path):
    store = HandoffStore(tmp_path / "nclaw")
    path = store.create(
        goal="task", model="llama3.2", estimated_tokens=10,
        context_window=1000, usage_ratio=0.01,
    )
    path.write_bytes(b" " * (store.MAX_HANDOFF_BYTES + 1))
    with pytest.raises(ValueError, match="size"):
        store.load(path.stem.removeprefix("handoff-"))


def test_handoff_load_rejects_symlink_file(tmp_path):
    store = HandoffStore(tmp_path / "nclaw")
    path = store.create(
        goal="task", model="llama3.2", estimated_tokens=10,
        context_window=1000, usage_ratio=0.01,
    )
    outside = tmp_path / "outside.json"
    outside.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.unlink()
    path.symlink_to(outside)
    with pytest.raises(ValueError, match="unavailable or unsafe"):
        store.load(path.stem.removeprefix("handoff-"))
