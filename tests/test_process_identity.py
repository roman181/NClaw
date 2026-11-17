"""Tests for read-only local process liveness diagnostics."""

from core.process_identity import execution_process_state


def _write_stat(proc_root, pid, start_token):
    process_dir = proc_root / str(pid)
    process_dir.mkdir(parents=True, exist_ok=True)
    # /proc/PID/stat fields after the final ')' start at field 3 (state).
    fields = ["S"] + ["0"] * 18 + [str(start_token)]
    (process_dir / "stat").write_text(
        f"{pid} (nclaw test worker) {' '.join(fields)}",
        encoding="ascii",
    )


def test_process_identity_matches_pid_and_start_token(tmp_path):
    _write_stat(tmp_path, 42, 12345)
    assert execution_process_state(42, "12345", tmp_path) == "active"


def test_reused_pid_is_reported_as_interrupted(tmp_path):
    _write_stat(tmp_path, 42, 99999)
    assert execution_process_state(42, "12345", tmp_path) == "interrupted"


def test_missing_process_is_reported_as_interrupted(tmp_path):
    assert execution_process_state(42, "12345", tmp_path) == "interrupted"


def test_unreadable_or_invalid_identity_remains_unknown(tmp_path):
    _write_stat(tmp_path, 42, "not-a-number")
    assert execution_process_state(42, "12345", tmp_path) == "unknown"
    assert execution_process_state(True, "12345", tmp_path) == "unknown"
    assert execution_process_state(42, None, tmp_path) == "unknown"


def test_missing_proc_mount_is_unknown(tmp_path):
    assert execution_process_state(42, "12345", tmp_path / "no-proc") == "unknown"
