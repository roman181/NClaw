"""Atomic, private JSON handoff files for local NClaw continuation."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path


class HandoffStore:
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
            "created_at": datetime.now(timezone.utc).isoformat(),
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
