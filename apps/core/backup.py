"""
backup.py - Database backup and restore (SQLite)
================================================

Owner: Rajneesh Kumar (task R-16)

* Backup uses SQLite's own backup API (safe while the app is running).
* Restore needs the word RESTORE and first makes a safety copy.
* File names are checked so nobody can restore a file outside the backup folder.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.utils import timezone

from .exceptions import ConfirmationRequiredError, NotFoundError, ValidationError
from .models import BackupRecord
from .services import AuditService

NAME_RE = re.compile(r"^cyberquest_\d{8}_\d{6}(_[a-z]+)?(_\d+)?\.sqlite3$")
RESTORE_WORD = "RESTORE"
KEEP = 10


class BackupService:
    """Make, list and restore database backups."""

    def __init__(self, folder: Path | None = None):
        self.folder = Path(folder or settings.BASE_DIR / "backups")
        self.folder.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _db_path() -> Path:
        if connection.vendor != "sqlite":
            raise ValidationError("In-app backup works with SQLite. For PostgreSQL use pg_dump (see README).")
        name = settings.DATABASES["default"]["NAME"]
        return Path(str(name))

    def create(self, user=None, reason: str = "manual") -> BackupRecord:
        """Copy the live database into backups/."""
        stamp = timezone.localtime().strftime("%Y%m%d_%H%M%S")
        base = f"cyberquest_{stamp}_{re.sub(r'[^a-z]', '', reason.lower()) or 'manual'}"
        target, n = self.folder / f"{base}.sqlite3", 2
        while target.exists():
            target, n = self.folder / f"{base}_{n}.sqlite3", n + 1
        connection.ensure_connection()
        dest = sqlite3.connect(target)
        try:
            connection.connection.backup(dest)
        finally:
            dest.close()
        record = BackupRecord.objects.create(
            file_name=target.name,
            size_bytes=target.stat().st_size,
            reason=reason,
            created_by=getattr(user, "username", "system"),
        )
        AuditService.log(user, "backup_created", target.name)
        self._prune()
        return record

    def _prune(self) -> None:
        """Keep only the newest backups."""
        for old in BackupRecord.objects.all()[KEEP:]:
            (self.folder / old.file_name).unlink(missing_ok=True)
            old.delete()

    def path_for(self, name: str) -> Path:
        """Safe path for a backup name (blocks ../ tricks)."""
        if not NAME_RE.match(name or ""):
            raise ValidationError("That is not a CyberQuest backup file name.")
        path = (self.folder / name).resolve()
        if path.parent != self.folder.resolve() or not path.exists():
            raise NotFoundError("Backup file not found.")
        return path

    def restore(self, name: str, confirm: str, user=None) -> str:
        """Replace the live database with a backup (needs the word RESTORE)."""
        if (confirm or "").strip() != RESTORE_WORD:
            raise ConfirmationRequiredError(f"Please type {RESTORE_WORD} to confirm.")
        source = self.path_for(name)
        safety = self.create(user, "beforerestore").file_name
        src = sqlite3.connect(source)
        try:
            connection.ensure_connection()
            src.backup(connection.connection)
        finally:
            src.close()
        AuditService.log(user, "backup_restored", name, details=f"safety copy {safety}")
        return safety
