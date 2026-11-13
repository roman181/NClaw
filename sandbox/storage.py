"""Local NClaw storage layout and safe file intake."""
from __future__ import annotations

import hashlib
import os
import shutil
import uuid
from pathlib import Path

MAX_IMPORT_BYTES = 100 * 1024 * 1024
ALLOWED_TEXT_SUFFIXES = {".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".xml", ".html", ".css", ".js", ".py", ".toml", ".ini", ".log", ".rst"}
ALLOWED_DOCUMENT_SUFFIXES = {".pdf", ".zip"}


class LocalSandbox:
    """Creates the NClaw folders and copies inputs without executing them."""

    FOLDERS = ("incoming", "processing", "approved", "rejected", "quarantine", "library", "metadata")

    def __init__(self, root: str | Path | None = None) -> None:
        configured = root or os.getenv("NCLAW_DATA_DIR", "~/.nclaw")
        self.root = Path(configured).expanduser().resolve()
        self.ensure_layout()

    def ensure_layout(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            self.root.chmod(0o700)
        except OSError:
            pass
        for name in self.FOLDERS:
            folder = self.root / name
            folder.mkdir(mode=0o700, exist_ok=True)
            if folder.is_symlink() or not folder.resolve().is_relative_to(self.root):
                raise ValueError(f"Unsafe sandbox folder: {name}")
            try:
                folder.chmod(0o700)
            except OSError:
                pass

    def folder(self, name: str) -> Path:
        if name not in self.FOLDERS:
            raise ValueError("Unknown sandbox folder")
        return self.root / name

    def import_file(self, source: str | Path) -> dict[str, str | int]:
        source_path = Path(source).expanduser()
        if source_path.is_symlink() or not source_path.is_file():
            raise ValueError("Only regular, non-symlink files can be imported")
        size = source_path.stat().st_size
        if size <= 0 or size > MAX_IMPORT_BYTES:
            raise ValueError("File must be between 1 byte and 100 MiB")
        suffix = source_path.suffix.lower()
        trusted_type = suffix in ALLOWED_TEXT_SUFFIXES | ALLOWED_DOCUMENT_SUFFIXES
        target_folder = self.folder("incoming" if trusted_type else "quarantine")
        file_id = uuid.uuid4().hex
        safe_name = "".join(ch for ch in source_path.name if ch.isalnum() or ch in "._-")[:100]
        if not safe_name or safe_name in {".", ".."}:
            safe_name = "import.bin"
        target = target_folder / f"{file_id}_{safe_name}"
        digest = hashlib.sha256()
        with source_path.open("rb") as src, target.open("xb") as dst:
            while chunk := src.read(1024 * 1024):
                digest.update(chunk)
                dst.write(chunk)
        target.chmod(0o600)
        return {"id": file_id, "name": safe_name, "path": str(target), "size": size,
                "sha256": digest.hexdigest(), "status": "incoming" if trusted_type else "quarantine"}

    def move_to(self, source: str | Path, destination: str) -> Path:
        candidate = Path(source)
        if candidate.is_symlink():
            raise ValueError("Symbolic links are not accepted")
        source_path = candidate.resolve(strict=True)
        if not source_path.is_relative_to(self.root) or not source_path.is_file():
            raise ValueError("Source must be a regular file inside the sandbox")
        target_folder = self.folder(destination)
        target = target_folder / source_path.name
        if target.exists():
            raise FileExistsError("Destination already exists")
        return Path(shutil.move(str(source_path), str(target)))
