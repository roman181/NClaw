"""Local metadata-only skill registry; skill instructions are never executed as code."""
from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

SKILL_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
SEMVER = re.compile(r"^(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)$")
MAX_INSTRUCTIONS = 20_000


class SkillRegistry:
    """Stores versioned skill descriptions with explicit test and approval gates."""

    def __init__(self, data_root: str | Path | None = None) -> None:
        configured = data_root or os.getenv("NCLAW_DATA_DIR", "~/.nclaw")
        self.root = Path(configured).expanduser().resolve()
        self.directory = self.root / "library" / "skills"

    def _skill_path(self, skill_id: str, version: str) -> Path:
        if not SKILL_ID.fullmatch(skill_id):
            raise ValueError("Ungültige Skill-ID")
        if not SEMVER.fullmatch(version):
            raise ValueError("Version muss dem Format MAJOR.MINOR.PATCH entsprechen")
        return self.directory / skill_id / f"{version}.json"

    @staticmethod
    def _read(path: Path) -> dict[str, object]:
        if path.is_symlink() or not path.is_file():
            raise ValueError("Skill-Datei fehlt oder ist unsicher")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Ungültiges Skill-Format")
        return payload

    @staticmethod
    def _write(path: Path, payload: dict[str, object]) -> None:
        temporary = path.with_name(f".{uuid.uuid4().hex}.tmp")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=False, indent=2)
                stream.write("\\n")
            temporary.replace(path)
        finally:
            if temporary.exists():
                temporary.unlink()
        try:
            path.chmod(0o600)
        except OSError:
            pass

    def create_draft(
        self, *, skill_id: str, name: str, version: str,
        description: str, instructions: str, source: str = "local",
    ) -> Path:
        if not name.strip() or len(name) > 100:
            raise ValueError("Skill-Name muss 1 bis 100 Zeichen lang sein")
        if not description.strip() or len(description) > 1000:
            raise ValueError("Beschreibung muss 1 bis 1000 Zeichen lang sein")
        if not instructions.strip() or len(instructions) > MAX_INSTRUCTIONS:
            raise ValueError("Skill-Anweisungen müssen 1 bis 20000 Zeichen lang sein")
        if not source.strip() or len(source) > 200:
            raise ValueError("Ungültige Quellenangabe")
        if self.directory.is_symlink():
            raise ValueError("Skill-Bibliothek darf kein symbolischer Link sein")
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not self.directory.resolve().is_relative_to(self.root):
            raise ValueError("Skill-Bibliothek liegt außerhalb des lokalen Datenordners")
        target = self._skill_path(skill_id, version)
        target.parent.mkdir(mode=0o700, exist_ok=True)
        if target.parent.is_symlink() or not target.parent.resolve().is_relative_to(self.directory.resolve()):
            raise ValueError("Unsicherer Skill-Ordner")
        if target.exists() or target.is_symlink():
            raise FileExistsError("Diese Skill-Version existiert bereits")
        payload: dict[str, object] = {
            "schema_version": 1,
            "skill_id": skill_id,
            "name": name.strip(),
            "version": version,
            "description": description.strip(),
            "instructions": instructions,
            "source": source,
            "created_at": datetime.now(timezone.utc).isoformat(),  # noqa: UP017
            "status": "pending_approval",
            "tests_passed": False,
            "test_summary": "Noch nicht getestet",
            "approved_at": None,
        }
        self._write(target, payload)
        return target

    def record_test_result(self, skill_id: str, version: str, *, passed: bool, summary: str) -> dict[str, object]:
        path = self._skill_path(skill_id, version)
        payload = self._read(path)
        if payload.get("status") != "pending_approval":
            raise ValueError("Nur Skills im Freigabeprozess können getestet werden")
        if not summary.strip() or len(summary) > 1000:
            raise ValueError("Testzusammenfassung muss 1 bis 1000 Zeichen lang sein")
        payload["tests_passed"] = bool(passed)
        payload["test_summary"] = summary.strip()
        self._write(path, payload)
        return payload

    def approve(self, skill_id: str, version: str, *, approved: bool) -> dict[str, object]:
        if approved is not True:
            raise PermissionError("Explizite Freigabe ist erforderlich")
        path = self._skill_path(skill_id, version)
        payload = self._read(path)
        if payload.get("status") != "pending_approval":
            raise ValueError("Skill ist nicht mehr freigabefähig")
        if payload.get("tests_passed") is not True:
            raise PermissionError("Skill benötigt zuerst einen erfolgreichen Test")
        payload["status"] = "approved"
        payload["approved_at"] = datetime.now(timezone.utc).isoformat()  # noqa: UP017
        self._write(path, payload)
        return payload

    def reject(self, skill_id: str, version: str) -> dict[str, object]:
        path = self._skill_path(skill_id, version)
        payload = self._read(path)
        if payload.get("status") != "pending_approval":
            raise ValueError("Nur ausstehende Skills können abgelehnt werden")
        payload["status"] = "rejected"
        self._write(path, payload)
        return payload

    def list_active(self) -> list[dict[str, object]]:
        if not self.directory.exists():
            return []
        if self.directory.is_symlink():
            raise ValueError("Unsichere Skill-Bibliothek")
        active = []
        for path in sorted(self.directory.glob("*/*.json")):
            payload = self._read(path)
            if payload.get("status") == "approved":
                active.append({key: value for key, value in payload.items() if key != "instructions"})
        return active
