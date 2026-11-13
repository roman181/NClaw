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


def test_restore_rejects_non_nclaw_file_before_download(tmp_path, monkeypatch):
    class Request:
        def execute(self):
            return {
                "id": "abcde",
                "name": "other.txt",
                "parents": ["someone-else"],
                "size": "4",
                "appProperties": {"nclaw_backup": "true", "sha256": "0" * 64},
                "trashed": False,
            }

    class Files:
        def list(self, **kwargs):
            return type("Request", (), {"execute": lambda self: {"files": [{"id": "folder"}]}})()

        def get(self, **kwargs):
            return Request()

    class Service:
        def files(self):
            return Files()

    drive = GoogleDriveStorage(tmp_path / "data")
    monkeypatch.setattr(drive, "_service", lambda: Service())
    with pytest.raises(ValueError, match="Backup-Ordner"):
        drive.restore_to_quarantine("abcde")
    assert not list((tmp_path / "data").glob("quarantine/*")) if (tmp_path / "data" / "quarantine").exists() else True


def test_restore_verifies_hash_and_writes_only_to_quarantine(tmp_path, monkeypatch):
    import hashlib
    import sys
    import types

    payload = b"restored safely"
    digest = hashlib.sha256(payload).hexdigest()

    class Request:
        def execute(self):
            return {
                "id": "abcde",
                "name": "../unsafe name.txt",
                "parents": ["folder"],
                "size": str(len(payload)),
                "appProperties": {"nclaw_backup": "true", "sha256": digest},
                "trashed": False,
            }

    class Files:
        def list(self, **kwargs):
            return type("ListRequest", (), {"execute": lambda self: {"files": [{"id": "folder"}]}})()

        def get(self, **kwargs):
            return Request()

        def get_media(self, **kwargs):
            return object()

    class Service:
        def files(self):
            return Files()

    class Downloader:
        def __init__(self, buffer, request):
            self.buffer = buffer

        def next_chunk(self):
            self.buffer.write(payload)
            return None, True

    fake_http = types.ModuleType("googleapiclient.http")
    fake_http.MediaIoBaseDownload = Downloader
    monkeypatch.setitem(sys.modules, "googleapiclient.http", fake_http)

    drive = GoogleDriveStorage(tmp_path / "data")
    monkeypatch.setattr(drive, "_service", lambda: Service())
    result = drive.restore_to_quarantine("abcde")
    restored = Path(result["path"])
    assert result["status"] == "quarantine"
    assert restored.parent == tmp_path / "data" / "quarantine"
    assert restored.read_bytes() == payload
    assert result["sha256"] == digest
    assert ".." not in restored.name


def test_restore_rejects_invalid_file_id_without_connecting(tmp_path, monkeypatch):
    drive = GoogleDriveStorage(tmp_path / "data")
    monkeypatch.setattr(drive, "_service", lambda: pytest.fail("Drive must not be contacted"))
    with pytest.raises(ValueError, match="Datei-ID"):
        drive.restore_to_quarantine("bad/id")
