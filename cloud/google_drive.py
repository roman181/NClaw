"""Optional Google Drive backup for explicitly approved local files.

OAuth client credentials and refresh tokens must remain on the device. The
Drive scope is drive.file, limiting access to files created/opened by this app.
"""
from __future__ import annotations

import mimetypes
import os
from pathlib import Path


class GoogleDriveError(RuntimeError):
    """Raised when Drive configuration or upload fails."""


class GoogleDriveStorage:
    def __init__(self, sandbox_root: str | Path, credentials_file: str | Path | None = None,
                 token_file: str | Path | None = None, folder_name: str = "NClaw-Backup") -> None:
        self.root = Path(sandbox_root).expanduser().resolve()
        self.credentials_file = Path(credentials_file or os.getenv("GOOGLE_DRIVE_CREDENTIALS", "~/.nclaw/google-oauth-client.json")).expanduser()
        self.token_file = Path(token_file or os.getenv("GOOGLE_DRIVE_TOKEN", "~/.nclaw/google-drive-token.json")).expanduser()
        self.folder_name = folder_name

    def _service(self):
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise GoogleDriveError("Google-Drive-Pakete fehlen. Bitte requirements.txt installieren.") from exc
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
            credentials = flow.run_local_server(host="127.0.0.1", port=0, open_browser=False,
                                                authorization_prompt_message="Google-Anmeldung im Browser öffnen: {url}")
            self.token_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            self.token_file.write_text(credentials.to_json(), encoding="utf-8")
            try:
                self.token_file.chmod(0o600)
            except OSError:
                pass
        return build("drive", "v3", credentials=credentials, cache_discovery=False)

    def _folder_id(self, service) -> str:
        escaped = self.folder_name.replace("'", "\\\\'")
        response = service.files().list(q=f"mimeType='application/vnd.google-apps.folder' and name='{escaped}' and trashed=false",
                                        spaces="drive", fields="files(id,name)", pageSize=10).execute()
        if response.get("files"):
            return response["files"][0]["id"]
        from googleapiclient.http import MediaFileUpload
        metadata = {"name": self.folder_name, "mimeType": "application/vnd.google-apps.folder"}
        folder = service.files().create(body=metadata, fields="id").execute()
        return folder["id"]

    def upload_approved_file(self, file_path: str | Path) -> dict[str, str]:
        """Upload one file from sandbox/approved; never sync incoming automatically."""
        path = Path(file_path).expanduser().resolve(strict=True)
        approved = (self.root / "approved").resolve(strict=True)
        if not path.is_relative_to(approved) or not path.is_file() or path.is_symlink():
            raise ValueError("Nur reguläre Dateien aus dem Ordner approved dürfen hochgeladen werden")
        service = self._service()
        from googleapiclient.http import MediaFileUpload
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        folder_id = self._folder_id(service)
        metadata = {"name": path.name, "parents": [folder_id], "description": "NClaw approved local backup"}
        media = MediaFileUpload(str(path), mimetype=mime_type, resumable=True)
        result = service.files().create(body=metadata, media_body=media, fields="id,name,webViewLink").execute()
        return {"id": result["id"], "name": result["name"], "url": result.get("webViewLink", "")}
