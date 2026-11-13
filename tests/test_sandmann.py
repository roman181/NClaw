"""Tests for local sandbox intake and safe archive inspection."""
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
    result = agent.inspect(imported["path"])
    assert result["text"] == "Hallo NClaw"


def test_unknown_file_goes_to_quarantine(tmp_path):
    source = tmp_path / "payload.exe"
    source.write_bytes(b"not executed")
    agent = SandmannAgent(LocalSandbox(tmp_path / "data"))
    imported = agent.import_file(source)
    assert imported["status"] == "quarantine"
    assert "notice" in agent.inspect(imported["path"])


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
