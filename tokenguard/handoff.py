"""Atomic, private JSON handoff files for local NClaw continuation."""
from __future__ import annotations

import json
import os
import stat
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class HandoffStore:
    """Store version-1 handoffs locally; loading never resumes execution."""

    MAX_HANDOFF_BYTES = 64 * 1024
    _FIELDS = {
        "schema_version", "handoff_id", "created_at", "project", "model",
        "goal", "estimated_tokens", "context_window", "usage_ratio",
        "status", "notes",
    }

    def __init__(self, sandbox_root: str | Path) -> None:
        self.root = Path(sandbox_root).expanduser().resolve()
        self.directory = self.root / "metadata" / "handoffs"

    def create(self, *, goal: str, model: str, estimated_tokens: int,
               context_window: int, usage_ratio: float) -> Path:
        if not goal.strip() or not model.strip():
            raise ValueError("Handoff goal and model must not be empty")
        if estimated_tokens < 0 or context_window < 1 or not 0 <= usage_ratio <= 10:
            raise ValueError("Invalid handoff token metrics")
        metadata = self.root / "metadata"
        if metadata.is_symlink():
            raise ValueError("Unsafe metadata directory")
        metadata.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.directory.is_symlink():
            raise ValueError("Unsafe handoff directory")
        self.directory.mkdir(mode=0o700, exist_ok=True)
        if not self.directory.resolve().is_relative_to(self.root):
            raise ValueError("Handoff directory escaped local data root")
        handoff_id = uuid.uuid4().hex
        payload = {
            "schema_version": 1,
            "handoff_id": handoff_id,
            "created_at": datetime.now(timezone.utc).isoformat(),  # noqa: UP017
            "project": "NClaw",
            "model": model,
            "goal": goal,
            "estimated_tokens": estimated_tokens,
            "context_window": context_window,
            "usage_ratio": round(usage_ratio, 4),
            "status": "waiting_for_manual_resume",
            "notes": [
                "Token count is an estimate, not Ollama's exact tokenizer output.",
                "No model switch or external upload was performed.",
            ],
        }
        target = self.directory / f"handoff-{handoff_id}.json"
        temporary = self.directory / f".{handoff_id}.tmp"
        try:
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            temporary.replace(target)
        finally:
            if temporary.exists():
                temporary.unlink()
        try:
            target.chmod(0o600)
        except OSError:
            pass
        return target

    @staticmethod
    def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate handoff JSON key")
            result[key] = value
        return result

    @classmethod
    def _validate(cls, payload: Any, expected_id: str) -> dict[str, Any]:
        if not isinstance(payload, dict) or set(payload) != cls._FIELDS:
            raise ValueError("Invalid handoff fields")
        if type(payload["schema_version"]) is not int or payload["schema_version"] != 1:
            raise ValueError("Unsupported handoff schema version")
        if payload["handoff_id"] != expected_id or payload["project"] != "NClaw":
            raise ValueError("Handoff identity mismatch")
        if payload["status"] != "waiting_for_manual_resume":
            raise ValueError("Invalid handoff status")
        for field in ("goal", "model"):
            value = payload[field]
            if not isinstance(value, str) or not value.strip() or len(value) > 16_384:
                raise ValueError(f"Invalid handoff {field}")
        for field, minimum in (("estimated_tokens", 0), ("context_window", 1)):
            value = payload[field]
            if type(value) is not int or value < minimum:
                raise ValueError(f"Invalid handoff {field}")
        ratio = payload["usage_ratio"]
        if (
            isinstance(ratio, bool)
            or not isinstance(ratio, (int, float))
            or not 0 <= ratio <= 10
        ):
            raise ValueError("Invalid handoff usage ratio")
        try:
            datetime.fromisoformat(payload["created_at"])
        except (TypeError, ValueError):
            raise ValueError("Invalid handoff timestamp") from None
        notes = payload["notes"]
        if not isinstance(notes, list) or len(notes) > 32 or not all(
            isinstance(note, str) and len(note) <= 1024 for note in notes
        ):
            raise ValueError("Invalid handoff notes")
        return payload

    def load(self, handoff_id: str) -> dict[str, Any]:
        """Validate and return a handoff by UUID hex; never resumes it."""
        try:
            normalized_id = uuid.UUID(hex=handoff_id).hex
        except (ValueError, TypeError, AttributeError):
            raise ValueError("Invalid handoff ID") from None
        if normalized_id != handoff_id:
            raise ValueError("Invalid handoff ID")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        directory_flags = flags | getattr(os, "O_DIRECTORY", 0)
        metadata_fd = handoffs_fd = descriptor = None
        try:
            metadata_fd = os.open(self.root / "metadata", directory_flags)
            handoffs_fd = os.open("handoffs", directory_flags, dir_fd=metadata_fd)
            descriptor = os.open(
                f"handoff-{normalized_id}.json", flags, dir_fd=handoffs_fd
            )
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_size > self.MAX_HANDOFF_BYTES:
                raise ValueError("Invalid handoff file type or size")
            with os.fdopen(descriptor, "rb") as stream:
                descriptor = None
                raw = stream.read(self.MAX_HANDOFF_BYTES + 1)
        except OSError as exc:
            raise ValueError("Handoff file is unavailable or unsafe") from exc
        finally:
            for fd in (descriptor, handoffs_fd, metadata_fd):
                if fd is not None:
                    os.close(fd)
        if len(raw) > self.MAX_HANDOFF_BYTES:
            raise ValueError("Handoff file exceeds size limit")
        try:
            payload = json.loads(
                raw.decode("utf-8"), object_pairs_hook=self._reject_duplicate_keys
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError("Malformed handoff JSON") from exc
        return self._validate(payload, normalized_id)
