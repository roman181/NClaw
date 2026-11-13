"""Tests for workspace-confined, create-only file actions."""
import pytest

from core.approved_actions import ApprovedFileWriter


def test_creates_new_file_inside_workspace(tmp_path) -> None:
    writer = ApprovedFileWriter(tmp_path)
    path = writer.create_new("notes/hello.txt", "Hallo NClaw")
    assert path.read_text(encoding="utf-8") == "Hallo NClaw"
    assert path.stat().st_mode & 0o777 == 0o600


def test_refuses_traversal_and_absolute_paths(tmp_path) -> None:
    writer = ApprovedFileWriter(tmp_path)
    with pytest.raises(ValueError):
        writer.create_new("../outside.txt", "x")
    with pytest.raises(ValueError):
        writer.create_new("/tmp/outside.txt", "x")


def test_refuses_overwrite(tmp_path) -> None:
    writer = ApprovedFileWriter(tmp_path)
    writer.create_new("notes.txt", "original")
    with pytest.raises(FileExistsError):
        writer.create_new("notes.txt", "changed")
    assert (tmp_path / "notes.txt").read_text() == "original"


def test_refuses_secret_and_git_paths(tmp_path) -> None:
    writer = ApprovedFileWriter(tmp_path)
    with pytest.raises(ValueError):
        writer.create_new(".env", "SECRET=value")
    with pytest.raises(ValueError):
        writer.create_new(".git/config", "unsafe")


def test_refuses_symlinked_parent(tmp_path) -> None:
    outside = tmp_path.parent / "nclaw-outside-test"
    outside.mkdir(exist_ok=True)
    (tmp_path / "linked").symlink_to(outside, target_is_directory=True)
    writer = ApprovedFileWriter(tmp_path)
    with pytest.raises(ValueError):
        writer.create_new("linked/file.txt", "x")
