"""Local NClaw storage layout and safe file intake."""
from __future__ import annotations

import hashlib
import os
import stat
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

    def _open_directory(self, path: Path) -> int:
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = -1
        try:
            fd = os.open(path, flags)
            info = os.fstat(fd)
            path_info = os.stat(path, follow_symlinks=False)
            resolved = path.resolve(strict=True)
            if (
                not stat.S_ISDIR(info.st_mode)
                or not stat.S_ISDIR(path_info.st_mode)
                or stat.S_ISLNK(path_info.st_mode)
                or (info.st_dev, info.st_ino) != (path_info.st_dev, path_info.st_ino)
                or not resolved.is_relative_to(self.root)
            ):
                raise ValueError("Unsafe sandbox directory")
            return fd
        except Exception as exc:
            if fd >= 0:
                os.close(fd)
            if isinstance(exc, ValueError):
                raise
            raise ValueError("Unsafe sandbox directory") from exc

    def ensure_layout(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        root_fd = self._open_directory(self.root)
        try:
            os.fchmod(root_fd, 0o700)
        finally:
            os.close(root_fd)
        for name in self.FOLDERS:
            folder = self.root / name
            folder.mkdir(mode=0o700, exist_ok=True)
            folder_fd = self._open_directory(folder)
            try:
                os.fchmod(folder_fd, 0o700)
            finally:
                os.close(folder_fd)

    def folder(self, name: str) -> Path:
        if name not in self.FOLDERS:
            raise ValueError("Unknown sandbox folder")
        path = self.root / name
        try:
            info = os.stat(path, follow_symlinks=False)
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise ValueError(f"Unsafe sandbox folder: {name}") from exc
        if (
            not stat.S_ISDIR(info.st_mode)
            or stat.S_ISLNK(info.st_mode)
            or not resolved.is_relative_to(self.root)
        ):
            raise ValueError(f"Unsafe sandbox folder: {name}")
        return resolved

    def _open_folder(self, name: str) -> tuple[Path, int]:
        path = self.folder(name)
        return path, self._open_directory(path)

    def import_file(self, source: str | Path) -> dict[str, str | int]:
        source_path = Path(source).expanduser()
        if source_path.is_symlink():
            raise ValueError("Only regular, non-symlink files can be imported")

        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            source_fd = os.open(source_path, flags)
        except OSError as exc:
            raise ValueError("Only regular, non-symlink files can be imported") from exc

        folder_fd = -1
        try:
            source_info = os.fstat(source_fd)
            if not stat.S_ISREG(source_info.st_mode):
                raise ValueError("Only regular, non-symlink files can be imported")
            if source_info.st_size <= 0 or source_info.st_size > MAX_IMPORT_BYTES:
                raise ValueError(f"File must be between 1 byte and {MAX_IMPORT_BYTES} bytes")

            suffix = source_path.suffix.lower()
            trusted_type = suffix in ALLOWED_TEXT_SUFFIXES | ALLOWED_DOCUMENT_SUFFIXES
            folder_name = "incoming" if trusted_type else "quarantine"
            target_folder, folder_fd = self._open_folder(folder_name)

            file_id = uuid.uuid4().hex
            safe_name = "".join(ch for ch in source_path.name if ch.isalnum() or ch in "._-")[:100]
            if not safe_name or safe_name in {".", ".."}:
                safe_name = "import.bin"

            target_name = f"{file_id}_{safe_name}"
            temporary_name = f".{file_id}.part"
            target = target_folder / target_name
            digest = hashlib.sha256()
            copied = 0
            temporary_created = False
            target_published = False

            try:
                source_stream = os.fdopen(source_fd, "rb")
                source_fd = -1
                with source_stream as src:
                    temporary_fd = os.open(
                        temporary_name,
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                        0o600,
                        dir_fd=folder_fd,
                    )
                    temporary_created = True
                    try:
                        while chunk := src.read(1024 * 1024):
                            copied += len(chunk)
                            if copied > MAX_IMPORT_BYTES:
                                raise ValueError("File exceeds the import size limit")
                            digest.update(chunk)
                            view = memoryview(chunk)
                            while view:
                                written = os.write(temporary_fd, view)
                                view = view[written:]
                        os.fsync(temporary_fd)
                    finally:
                        os.close(temporary_fd)

                    final_info = os.fstat(src.fileno())
                    source_changed = (
                        copied != source_info.st_size
                        or final_info.st_size != source_info.st_size
                        or final_info.st_dev != source_info.st_dev
                        or final_info.st_ino != source_info.st_ino
                        or final_info.st_mtime_ns != source_info.st_mtime_ns
                        or final_info.st_ctime_ns != source_info.st_ctime_ns
                    )
                    if source_changed:
                        raise ValueError("Source changed during import")

                reservation_fd = os.open(
                    target_name,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=folder_fd,
                )
                os.close(reservation_fd)
                target_published = True
                os.replace(temporary_name, target_name, src_dir_fd=folder_fd, dst_dir_fd=folder_fd)
                temporary_created = False
                try:
                    os.fsync(folder_fd)
                except OSError:
                    pass
            except Exception:
                for name, created in ((temporary_name, temporary_created), (target_name, target_published)):
                    if created:
                        try:
                            os.unlink(name, dir_fd=folder_fd)
                        except FileNotFoundError:
                            pass
                raise
        finally:
            if source_fd >= 0:
                os.close(source_fd)
            if folder_fd >= 0:
                os.close(folder_fd)

        return {
            "id": file_id,
            "name": safe_name,
            "path": str(target),
            "size": copied,
            "sha256": digest.hexdigest(),
            "status": "incoming" if trusted_type else "quarantine",
        }

    def move_to(self, source: str | Path, destination: str) -> Path:
        candidate = Path(source)
        if candidate.is_symlink():
            raise ValueError("Symbolic links are not accepted")
        source_path = candidate.resolve(strict=True)
        if not source_path.is_relative_to(self.root) or not source_path.is_file():
            raise ValueError("Source must be a regular file inside the sandbox")
        target_folder, target_dir_fd = self._open_folder(destination)
        if source_path.parent == target_folder:
            os.close(target_dir_fd)
            raise ValueError("Source is already in the destination folder")

        source_dir_fd = -1
        source_fd = -1
        temporary_fd = -1
        temporary_created = False
        target_published = False
        source_removed = False
        target_name = source_path.name
        temporary_name = f".move-{uuid.uuid4().hex}.part"
        try:
            source_dir_fd = self._open_directory(source_path.parent)
            source_fd = os.open(
                target_name,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=source_dir_fd,
            )
            source_info = os.fstat(source_fd)
            entry_info = os.stat(target_name, dir_fd=source_dir_fd, follow_symlinks=False)
            if not stat.S_ISREG(source_info.st_mode) or stat.S_ISLNK(entry_info.st_mode):
                raise ValueError("Source must be a regular, non-symlink file")
            if (source_info.st_dev, source_info.st_ino) != (entry_info.st_dev, entry_info.st_ino):
                raise ValueError("Source changed before move")
            if source_info.st_size > MAX_IMPORT_BYTES:
                raise ValueError("File exceeds the sandbox move size limit")

            temporary_fd = os.open(
                temporary_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=target_dir_fd,
            )
            temporary_created = True
            copied = 0
            while chunk := os.read(source_fd, 1024 * 1024):
                copied += len(chunk)
                if copied > MAX_IMPORT_BYTES:
                    raise ValueError("File exceeds the sandbox move size limit")
                view = memoryview(chunk)
                while view:
                    written = os.write(temporary_fd, view)
                    view = view[written:]
            os.fsync(temporary_fd)
            os.close(temporary_fd)
            temporary_fd = -1

            final_info = os.fstat(source_fd)
            entry_after = os.stat(target_name, dir_fd=source_dir_fd, follow_symlinks=False)
            if (
                copied != source_info.st_size
                or final_info.st_size != source_info.st_size
                or final_info.st_dev != source_info.st_dev
                or final_info.st_ino != source_info.st_ino
                or final_info.st_mtime_ns != source_info.st_mtime_ns
                or final_info.st_ctime_ns != source_info.st_ctime_ns
                or (entry_after.st_dev, entry_after.st_ino) != (source_info.st_dev, source_info.st_ino)
            ):
                raise ValueError("Source changed during move")

            reservation_fd = os.open(
                target_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=target_dir_fd,
            )
            os.close(reservation_fd)
            target_published = True
            os.replace(temporary_name, target_name, src_dir_fd=target_dir_fd, dst_dir_fd=target_dir_fd)
            temporary_created = False
            os.unlink(target_name, dir_fd=source_dir_fd)
            source_removed = True
            for directory_fd in (source_dir_fd, target_dir_fd):
                try:
                    os.fsync(directory_fd)
                except OSError:
                    pass
            return target_folder / target_name
        except Exception:
            if not source_removed:
                for name, created in ((temporary_name, temporary_created), (target_name, target_published)):
                    if created:
                        try:
                            os.unlink(name, dir_fd=target_dir_fd)
                        except FileNotFoundError:
                            pass
            raise
        finally:
            for fd in (source_fd, temporary_fd, source_dir_fd, target_dir_fd):
                if fd >= 0:
                    os.close(fd)
