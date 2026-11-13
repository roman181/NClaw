"""Explicit Google Drive backup and quarantine-only restore for NClaw.

Only manually approved local files may be uploaded. Restores are written to
local quarantine and are never extracted, executed, or promoted automatically.
"""
from __future__ import annotations

import hashlib
import io
import mimetypes
import os
import re
import uuid
from pathlib import Path

MAX_BACKUP_BYTES = 100 * 1024 * 1024


class GoogleDriveError(RuntimeError):
    """Raised when Drive configuration or an operation fails."""


class GoogleDriveStorage:
    def __init__(
        self,
        sandbox_root: str | Path,
        credentials_file: str | Path | None = None,
        token_file: str | Path | None = None,
        folder_name: str = "NClaw-Backup",
    ) -> None:
        self.root = Path(sandbox_root).expanduser().resolve()
        self.credentials_file = Path(
            credentials_file
            or os.getenv("GOOGLE_DRIVE_CREDENTIALS", "~/.nclaw/google-oauth-client.json")
        ).expanduser()
        self.token_file = Path(
            token_file or os.getenv("GOOGLE_DRIVE_TOKEN", "~/.nclaw/google-drive-token.json")
        ).expanduser()
        self.folder_name = folder_name

    def _service(self):
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise GoogleDriveError(
                "Google-Drive-Pakete fehlen. Bitte requirements.txt installieren."
            ) from exc
        if not self.credentials_file.is_file():
            raise GoogleDriveError(f"OAuth-Clientdatei fehlt: {self.credentials_file}")
        scopes = ["https://www.googleapis.com/auth/drive.file"]
        credentials = None
        if self.token_file.is_file():
            credentials = Credentials.from_authorized_user_file(str(self.token_file), scopes)
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        if not credentials or not credentials.valid:
            flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_file), scopes)
            credentials = flow.run_local_server(
                host="127.0.0.1",
                port=0,
                open_browser=False,
                authorization_prompt_message="Google-Anmeldung im Browser öffnen: {url}",
            )
            self.token_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            self.token_file.write_text(credentials.to_json(), encoding="utf-8")
            try:
                self.token_file.chmod(0o600)
            except OSError:
                pass
        return build("drive", "v3", credentials=credentials, cache_discovery=False)

    def _folder_id(self, service) -> str:
        escaped = self.folder_name.replace("\\", "\\\\").replace("'", "\\'")
        response = service.files().list(
            q=(
                "mimeType='application/vnd.google-apps.folder' "
                f"and name='{escaped}' and trashed=false"
            ),
            spaces="drive",
            fields="files(id,name)",
            pageSize=10,
        ).execute()
        if response.get("files"):
            return response["files"][0]["id"]
        metadata = {"name": self.folder_name, "mimeType": "application/vnd.google-apps.folder"}
        return service.files().create(body=metadata, fields="id").execute()["id"]

    @staticmethod
    def _safe_name(name: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", Path(name).name)[:100]
        if cleaned in {"", ".", ".."}:
            return "restored-file.bin"
        return cleaned

    def upload_approved_file(self, file_path: str | Path) -> dict[str, str]:
        """Upload one regular file from sandbox/approved after explicit invocation."""
        candidate = Path(file_path).expanduser()
        if candidate.is_symlink():
            raise ValueError("Symbolische Links dürfen nicht hochgeladen werden")
        approved_candidate = self.root / "approved"
        if approved_candidate.is_symlink():
            raise ValueError("Der approved-Ordner darf kein symbolischer Link sein")
        path = candidate.resolve(strict=True)
        approved = approved_candidate.resolve(strict=True)
        if not path.is_relative_to(approved) or not path.is_file():
            raise ValueError("Nur reguläre Dateien aus dem Ordner approved dürfen hochgeladen werden")
        size = path.stat().st_size
        if size <= 0 or size > MAX_BACKUP_BYTES:
            raise ValueError("Backup-Datei muss zwischen 1 Byte und 100 MiB groß sein")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        service = self._service()
        from googleapiclient.http import MediaFileUpload

        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        folder_id = self._folder_id(service)
        metadata = {
            "name": path.name,
            "parents": [folder_id],
            "description": "NClaw approved local backup",
            "appProperties": {"nclaw_backup": "true", "sha256": digest},
        }
        media = MediaFileUpload(str(path), mimetype=mime_type, resumable=True)
        result = service.files().create(
            body=metadata, media_body=media, fields="id,name,webViewLink"
        ).execute()
        return {
            "id": result["id"],
            "name": result["name"],
            "url": result.get("webViewLink", ""),
            "sha256": digest,
        }

    def list_backups(self) -> list[dict[str, str]]:
        """List only NClaw-marked backup files in the configured Drive folder."""
        service = self._service()
        folder_id = self._folder_id(service)
        response = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            spaces="drive",
            fields="files(id,name,size,appProperties,webViewLink)",
            pageSize=100,
            orderBy="name",
        ).execute()
        backups = []
        for item in response.get("files", []):
            properties = item.get("appProperties") or {}
            if properties.get("nclaw_backup") == "true":
                backups.append({
                    "id": item["id"],
                    "name": item.get("name", "unknown"),
                    "size": str(item.get("size", "unknown")),
                    "sha256": properties.get("sha256", ""),
                    "url": item.get("webViewLink", ""),
                })
        return backups

    def restore_to_quarantine(self, file_id: str) -> dict[str, str | int]:
        """Download a verified NClaw backup into quarantine; never trust it automatically."""
        if not file_id or not re.fullmatch(r"[A-Za-z0-9_-]{5,200}", file_id):
            raise ValueError("Ungültige Google-Drive-Datei-ID")
        service = self._service()
        folder_id = self._folder_id(service)
        metadata = service.files().get(
            fileId=file_id,
            fields="id,name,mimeType,parents,size,appProperties,trashed",
        ).execute()
        properties = metadata.get("appProperties") or {}
        if metadata.get("trashed") or folder_id not in metadata.get("parents", []):
            raise ValueError("Datei gehört nicht zum NClaw-Backup-Ordner")
        expected_hash = properties.get("sha256", "")
        if properties.get("nclaw_backup") != "true" or not re.fullmatch(
            r"[a-f0-9]{64}", expected_hash
        ):
            raise ValueError("Datei besitzt keine gültigen NClaw-Backup-Metadaten")
        declared_size = int(metadata.get("size", 0))
        if declared_size <= 0 or declared_size > MAX_BACKUP_BYTES:
            raise ValueError("Drive-Datei überschreitet das Restore-Limit von 100 MiB")

        from googleapiclient.http import MediaIoBaseDownload

        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(
            buffer, service.files().get_media(fileId=file_id)
        )
        done = False
        while not done:
            _, done = downloader.next_chunk()
            if buffer.tell() > MAX_BACKUP_BYTES:
                raise ValueError("Download überschreitet das Restore-Limit von 100 MiB")
        payload = buffer.getvalue()
        if len(payload) != declared_size:
            raise GoogleDriveError("Downloadgröße stimmt nicht mit Drive-Metadaten überein")
        actual_hash = hashlib.sha256(payload).hexdigest()
        if actual_hash != expected_hash:
            raise GoogleDriveError("SHA-256-Prüfung fehlgeschlagen; Datei wird nicht gespeichert")

        quarantine = self.root / "quarantine"
        if quarantine.is_symlink() or not quarantine.resolve().is_relative_to(self.root):
            raise ValueError("Unsicherer Quarantäneordner")
        quarantine.mkdir(parents=True, exist_ok=True, mode=0o700)
        target = quarantine / f"drive_{uuid.uuid4().hex}_{self._safe_name(metadata.get('name', 'backup.bin'))}"
        with target.open("xb") as stream:
            stream.write(payload)
        try:
            target.chmod(0o600)
        except OSError:
            pass
        return {
            "path": str(target),
            "name": metadata.get("name", target.name),
            "size": len(payload),
            "sha256": actual_hash,
            "status": "quarantine",
        }


def main() -> None:
    """Explicit CLI for backup listing, upload, and quarantine-only restore."""
    import argparse

    from dotenv import load_dotenv

    from sandbox.storage import LocalSandbox

    load_dotenv()
    parser = argparse.ArgumentParser(description="NClaw: kontrolliertes Google-Drive-Backup")
    subparsers = parser.add_subparsers(dest="command", required=True)
    upload_parser = subparsers.add_parser("upload", help="Freigegebene lokale Datei sichern")
    upload_parser.add_argument("--file", required=True, help="Datei in sandbox/approved")
    subparsers.add_parser("list", help="NClaw-Backups in Google Drive anzeigen")
    restore_parser = subparsers.add_parser("restore", help="Backup in lokale Quarantäne laden")
    restore_parser.add_argument("--id", required=True, help="Google-Drive-Datei-ID")
    args = parser.parse_args()

    storage = LocalSandbox()
    drive = GoogleDriveStorage(storage.root)
    if args.command == "upload":
        result = drive.upload_approved_file(args.file)
        print(f"Upload erfolgreich: {result['name']} (SHA-256: {result['sha256']})")
    elif args.command == "list":
        for item in drive.list_backups():
            print(f"{item['id']}  {item['name']}  {item['size']} Bytes  SHA-256: {item['sha256']}")
    else:
        result = drive.restore_to_quarantine(args.id)
        print(f"Wiederhergestellt nach Quarantäne: {result['path']}")
        print(f"SHA-256 geprüft: {result['sha256']}")


if __name__ == "__main__":
    main()
