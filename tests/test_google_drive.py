"""Google Drive adapter must only accept manually approved sandbox files."""
import pytest

from cloud.google_drive import GoogleDriveStorage


def test_drive_upload_refuses_files_outside_approved(tmp_path):
    root = tmp_path / "data"
    (root / "approved").mkdir(parents=True)
    incoming = root / "incoming.txt"
    incoming.write_text("private", encoding="utf-8")
    drive = GoogleDriveStorage(root)
    with pytest.raises(ValueError):
        drive.upload_approved_file(incoming)


def test_drive_upload_refuses_symlinks(tmp_path):
    root = tmp_path / "data"
    approved = root / "approved"
    approved.mkdir(parents=True)
    original = approved / "original.txt"
    original.write_text("safe", encoding="utf-8")
    link = approved / "link.txt"
    link.symlink_to(original)
    drive = GoogleDriveStorage(root)
    with pytest.raises(ValueError):
        drive.upload_approved_file(link)
