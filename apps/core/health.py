"""
health.py - Health check used by Docker, run.bat and the System status page
===========================================================================

Owner: Rajneesh Kumar (task R-15)

Each check returns (ok, detail). /health/ answers HTTP 200 when the important
checks pass, otherwise 503, so Docker can restart the app.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.utils import timezone


def check_database() -> tuple[bool, str]:
    """Can we read from the database?"""
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
        return True, connection.vendor
    except Exception as exc:  # pylint: disable=broad-except
        return False, str(exc)[:120]


def check_disk() -> tuple[bool, str]:
    """Free space where CyberQuest writes its data (the database folder).

    On a school laptop this is the project disk. On Vercel the project folder is read-only and data lives in
    /tmp (about 500 MB), so the limit there is 100 MB instead of 0.5 GB.
    """
    folder = Path(str(settings.DATABASES["default"].get("NAME", settings.BASE_DIR))).parent
    usage = shutil.disk_usage(folder if folder.exists() else settings.BASE_DIR)
    free_gb = usage.free / 1024**3
    limit_gb = 0.1 if os.environ.get("VERCEL") else 0.5
    return free_gb > limit_gb, f"{free_gb:.1f} GB free"


def check_media() -> tuple[bool, str]:
    """Can we write to the media folder?"""
    folder = Path(settings.MEDIA_ROOT)
    try:
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=folder):
            pass
        return True, "writable"
    except OSError as exc:
        return False, str(exc)[:120]


def check_integrations() -> dict[str, str]:
    """Status of outside services (never fails the health check - they are optional)."""
    try:
        from apps.integrations.services import IntegrationService  # pylint: disable=import-outside-toplevel

        return IntegrationService().status_summary()
    except Exception:  # pylint: disable=broad-except
        return {}


def run_all() -> dict:
    """Run every check and return a dictionary (also used as JSON)."""
    checks = {"database": check_database(), "disk": check_disk(), "media": check_media()}
    healthy = all(ok for ok, _ in checks.values())
    return {
        "status": "ok" if healthy else "error",
        "version": settings.PROJECT["version"],
        "time": timezone.localtime().isoformat(timespec="seconds"),
        "checks": {name: {"ok": ok, "detail": detail} for name, (ok, detail) in checks.items()},
        "integrations": check_integrations(),
    }
