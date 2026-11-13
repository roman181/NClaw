"""Restricted file creation for explicitly approved NClaw actions."""
from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
from typing import ClassVar


class ApprovedFileWriter:
    """Create new UTF-8 files beneath one workspace; never overwrite files."""

    BLOCKED_PARTS: ClassVar[set[str]] = {".git", ".venv", "__pycache__", "node_modules"}
    BLOCKED_NAMES: ClassVar[set[str]] = {".env", ".env.local", ".env.production"}

    def __init__(self, workspace: str | Path) -> None:
        root = Path(workspace).expanduser()
        root.mkdir(parents=True, exist_ok=True)
        self.root = root.resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError("Workspace must be a directory")

    def validate_path(self, relative_path: str) -> Path:
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise ValueError("A relative file path is required")
        if "\\" in relative_path:
            raise ValueError("Backslashes are not allowed in workspace paths")
        rel = PurePosixPath(relative_path)
        if not rel.parts or rel.is_absolute() or any(part in {"", ".", ".."} for part in rel.parts):
            raise ValueError("Path must stay inside the workspace")
        if any(part in self.BLOCKED_PARTS for part in rel.parts):
            raise ValueError("This workspace path is protected")
        if rel.name in self.BLOCKED_NAMES or rel.name.startswith(".env."):
            raise ValueError("Environment files are protected")

        current = self.root
        for part in rel.parts[:-1]:
            current = current / part
            if current.is_symlink():
                raise ValueError("Symbolic-link directories are not allowed")
            if not current.exists() or not current.is_dir():
                raise ValueError("Parent directories must already exist")
        target = current / rel.name
        if target.is_symlink():
            raise ValueError("Symbolic-link targets are not allowed")
        if target.exists():
            raise FileExistsError("The target already exists; overwriting is disabled")
        return target

    def create_new(self, relative_path: str, content: str) -> Path:
        if not isinstance(content, str):
            raise TypeError("File content must be text")
        target = self.validate_path(relative_path)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(target, flags, 0o600)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        except (OSError, UnicodeError):
            try:
                target.unlink(missing_ok=True)
            finally:
                raise
        return target
