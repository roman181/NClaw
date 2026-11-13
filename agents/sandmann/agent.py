"""Sandmann safely inspects files; imported code is never executed."""
from __future__ import annotations

import hashlib
import json
import stat
import zipfile
from pathlib import Path, PurePosixPath

from sandbox.storage import LocalSandbox, MAX_IMPORT_BYTES

MAX_ZIP_FILES = 500
MAX_ZIP_UNPACKED_BYTES = 100 * 1024 * 1024
MAX_TEXT_READ_BYTES = 2 * 1024 * 1024


class SandmannAgent:
    def __init__(self, storage: LocalSandbox | None = None) -> None:
        self.storage = storage or LocalSandbox()

    def import_file(self, source: str | Path) -> dict[str, str | int]:
        """Copy a file into incoming or quarantine and return its fingerprint."""
        return self.storage.import_file(source)

    def inspect(self, stored_path: str | Path) -> dict[str, object]:
        path = Path(stored_path).resolve(strict=True)
        if not path.is_relative_to(self.storage.root) or not path.is_file() or path.is_symlink():
            raise ValueError("File must be inside the local sandbox")
        suffix = path.suffix.lower()
        result: dict[str, object] = {"name": path.name, "size": path.stat().st_size, "sha256": self._hash(path)}
        if suffix == ".zip":
            result["archive"] = self._inspect_zip(path)
        elif suffix == ".pdf":
            result["text"] = self._read_pdf(path)
        elif suffix in {".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".xml", ".html", ".css", ".js", ".py", ".toml", ".ini", ".log", ".rst"}:
            result["text"] = self._read_text(path)
        else:
            result["notice"] = "Dateityp wird nur aufbewahrt, nicht interpretiert."
        return result

    @staticmethod
    def _hash(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _read_text(path: Path) -> str:
        if path.stat().st_size > MAX_TEXT_READ_BYTES:
            raise ValueError("Textdatei ist größer als 2 MiB; Vorschau verweigert")
        return path.read_text(encoding="utf-8", errors="replace")

    @staticmethod
    def _read_pdf(path: Path) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF-Unterstützung fehlt: pypdf installieren") from exc
        reader = PdfReader(str(path), strict=True)
        if reader.is_encrypted:
            raise ValueError("Verschlüsselte PDFs werden nicht automatisch geöffnet")
        pages = []
        for page in reader.pages[:100]:
            pages.append(page.extract_text() or "")
        return "\n\n".join(pages)[:MAX_TEXT_READ_BYTES]

    @staticmethod
    def _inspect_zip(path: Path) -> dict[str, object]:
        files: list[str] = []
        total = 0
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ZIP_FILES:
                raise ValueError("ZIP enthält zu viele Einträge")
            for entry in entries:
                name = entry.filename.replace("\\\\", "/")
                member = PurePosixPath(name)
                mode = entry.external_attr >> 16
                if member.is_absolute() or any(part in {"", ".", ".."} for part in member.parts):
                    raise ValueError("Unsicherer ZIP-Pfad erkannt")
                if stat.S_ISLNK(mode):
                    raise ValueError("ZIP-Symlinks werden nicht akzeptiert")
                if entry.flag_bits & 0x1:
                    raise ValueError("Verschlüsselte ZIP-Einträge werden nicht akzeptiert")
                total += entry.file_size
                if total > MAX_ZIP_UNPACKED_BYTES:
                    raise ValueError("ZIP überschreitet das Entpack-Limit von 100 MiB")
                if entry.file_size and entry.compress_size == 0:
                    raise ValueError("Ungültige ZIP-Kompressionsangabe")
                if entry.compress_size and entry.file_size / entry.compress_size > 1000:
                    raise ValueError("Verdächtig hohe ZIP-Kompressionsrate")
                if not entry.is_dir():
                    files.append(name)
        return {"file_count": len(files), "unpacked_bytes": total, "files": files}
