"""Tests for local sandbox intake and safe archive inspection."""
import hashlib
import os
import zipfile

import pytest

from agents.sandmann import SandmannAgent
from sandbox.storage import LocalSandbox


def test_storage_layout_is_created_with_private_folders(tmp_path):
    storage = LocalSandbox(tmp_path / "device-data")
    assert all((storage.root / folder).is_dir() for folder in storage.FOLDERS)


def test_import_text_file_and_inspect(tmp_path):
    source = tmp_path / "hello.txt"
    source.write_text("Hallo NClaw", encoding="utf-8")
    agent = SandmannAgent(LocalSandbox(tmp_path / "data"))
    imported = agent.import_file(source)
    assert imported["status"] == "incoming"
    assert imported["size"] == len("Hallo NClaw".encode("utf-8"))
    assert imported["sha256"] == hashlib.sha256(b"Hallo NClaw").hexdigest()
    result = agent.inspect(imported["path"])
    assert result["text"] == "Hallo NClaw"


def test_import_rejects_symlink_source(tmp_path):
    source = tmp_path / "real.txt"
    source.write_text("not a link", encoding="utf-8")
    alias = tmp_path / "alias.txt"
    alias.symlink_to(source)
    storage = LocalSandbox(tmp_path / "data")

    with pytest.raises(ValueError, match="non-symlink"):
        storage.import_file(alias)

    assert list(storage.folder("incoming").iterdir()) == []


def test_import_rejects_source_growth_and_removes_partial_copy(tmp_path, monkeypatch):
    source = tmp_path / "growing.txt"
    size_limit = 1024 * 1024
    source.write_bytes(b"x" * size_limit)
    storage = LocalSandbox(tmp_path / "data")
    monkeypatch.setattr("sandbox.storage.MAX_IMPORT_BYTES", size_limit)
    real_fdopen = os.fdopen

    class GrowingReader:
        def __init__(self, stream):
            self.stream = stream
            self.grown = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self.stream.close()

        def read(self, size=-1):
            chunk = self.stream.read(size)
            if not self.grown:
                with source.open("ab") as changed:
                    changed.write(b"y")
                self.grown = True
            return chunk

    def fdopen_with_growth(fd, mode):
        return GrowingReader(real_fdopen(fd, mode))

    monkeypatch.setattr("sandbox.storage.os.fdopen", fdopen_with_growth)

    with pytest.raises(ValueError, match="import size limit"):
        storage.import_file(source)

    assert list(storage.folder("incoming").iterdir()) == []


def test_unknown_file_goes_to_quarantine(tmp_path):
    source = tmp_path / "payload.exe"
    source.write_bytes(b"not executed")
    agent = SandmannAgent(LocalSandbox(tmp_path / "data"))
    imported = agent.import_file(source)
    assert imported["status"] == "quarantine"
    result = agent.inspect(imported["path"])
    assert "notice" in result


def test_zip_inspection_lists_members_without_extracting(tmp_path):
    source = tmp_path / "sample.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("docs/readme.txt", "Hello")
    agent = SandmannAgent(LocalSandbox(tmp_path / "data"))
    imported = agent.import_file(source)
    result = agent.inspect(imported["path"])
    assert result["archive"]["files"] == ["docs/readme.txt"]
    assert not (tmp_path / "data" / "processing" / "docs").exists()


def test_zip_path_traversal_is_rejected(tmp_path):
    source = tmp_path / "bad.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("../escape.txt", "no")
    agent = SandmannAgent(LocalSandbox(tmp_path / "data"))
    imported = agent.import_file(source)
    with pytest.raises(ValueError):
        agent.inspect(imported["path"])


def test_move_only_accepts_files_inside_sandbox(tmp_path):
    storage = LocalSandbox(tmp_path / "data")
    source = tmp_path / "note.md"
    source.write_text("ok", encoding="utf-8")
    imported = storage.import_file(source)
    moved = storage.move_to(imported["path"], "approved")
    assert moved.parent == storage.folder("approved")
