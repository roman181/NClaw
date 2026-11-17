"""Best-effort process identity diagnostics for local agent execution audits.

Linux and Android expose a process start-time token through /proc. The token
prevents a reused PID from being mistaken for the original live process.
"""

from __future__ import annotations

import os
from pathlib import Path


def _read_start_token(pid: int, proc_root: Path) -> str | None:
    try:
        stat = (proc_root / str(pid) / "stat").read_text(encoding="ascii")
    except (OSError, UnicodeError):
        return None

    closing = stat.rfind(")")
    if closing < 0:
        return None
    fields = stat[closing + 1 :].split()
    if len(fields) <= 19:
        return None
    token = fields[19]
    return token if token.isdecimal() else None


def current_process_identity() -> tuple[int, str | None]:
    """Return this process PID and its Linux/Android start-time token."""
    pid = os.getpid()
    return pid, _read_start_token(pid, Path("/proc"))


def execution_process_state(
    pid: object,
    start_token: object,
    proc_root: Path = Path("/proc"),
) -> str:
    """Classify a recorded process without changing execution or audit state.

    A missing PID or a different start token means the original process is no
    longer present. Unsupported or unreadable /proc data remains unknown.
    """
    if (
        not isinstance(pid, int)
        or isinstance(pid, bool)
        or pid <= 0
        or not isinstance(start_token, str)
        or not start_token.isdecimal()
    ):
        return "unknown"
    if not proc_root.is_dir():
        return "unknown"

    try:
        stat = (proc_root / str(pid) / "stat").read_text(encoding="ascii")
    except FileNotFoundError:
        return "interrupted"
    except (OSError, UnicodeError):
        return "unknown"

    closing = stat.rfind(")")
    if closing < 0:
        return "unknown"
    fields = stat[closing + 1 :].split()
    if len(fields) <= 19 or not fields[19].isdecimal():
        return "unknown"
    return "active" if fields[19] == start_token else "interrupted"
