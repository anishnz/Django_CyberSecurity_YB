"""
vercel.py - Settings for the online demo on Vercel (https://cyber-yb.vercel.app)
================================================================================

Owner: Anish Shrestha (Lead Software Engineer)

Vercel runs CyberQuest as one serverless function. Its project folder is
read-only, and only /tmp can be written. So this file:

* keeps the SQLite database, uploads and logs in /tmp,
* trusts Vercel's HTTPS proxy and uses secure cookies,
* lets every *.vercel.app address (and an optional custom domain) reach the app.

The database in /tmp is a copy of a demo database made during the build
(see ``scripts/vercel_build.py``). It is reset when Vercel starts a new
instance, which is fine for a public demo: no real student data is ever kept.
"""

import os
import secrets
from pathlib import Path as _Path

# Secret key: a value set in the Vercel project settings wins. Otherwise use the random key that
# scripts/vercel_build.py writes into this deployment (never into Git). During the very first
# build steps that file does not exist yet, so a throw-away random key is used for those commands.
_KEY_FILE = _Path(__file__).resolve().parent.parent.parent / "vercel_seed" / "secret_key.txt"
if not os.environ.get("DJANGO_SECRET_KEY"):
    os.environ["DJANGO_SECRET_KEY"] = (
        _KEY_FILE.read_text(encoding="utf-8").strip() if _KEY_FILE.is_file() else secrets.token_urlsafe(50)
    )

# These must be set before base.py is imported, because base.py reads them.
os.environ.setdefault("SQLITE_PATH", "/tmp/cyberquest/cyberquest.sqlite3")
os.environ.setdefault("MEDIA_ROOT", "/tmp/cyberquest/media")
os.environ.setdefault("LOG_DIR", "/tmp/cyberquest/logs")
os.environ.setdefault("SITE_URL", "https://cyber-yb.vercel.app")

from .base import *  # noqa: E402,F401,F403  # pylint: disable=wildcard-import,unused-wildcard-import,wrong-import-position
from .base import env  # noqa: E402  # pylint: disable=wrong-import-position

DEBUG = False

# Entry point that prepares the demo database in /tmp before the first request.
WSGI_APPLICATION = "cyberquest.wsgi_vercel.application"

# Vercel gives every deployment its own *.vercel.app address.
ALLOWED_HOSTS = [".vercel.app", "localhost", "127.0.0.1"] + [
    h.strip() for h in env("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()
]
CSRF_TRUSTED_ORIGINS = ["https://*.vercel.app"] + [
    o.strip() for o in env("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]

# Vercel ends HTTPS at its edge and passes the request on with this header.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # vercel.app is HTTPS only

# Vercel collects static files during the build and serves them from its CDN.
# WhiteNoise (with finders) is only a safety net if a file is asked for directly.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
WHITENOISE_USE_FINDERS = True

# Backups also go to /tmp (the project folder is read-only on Vercel).
BACKUP_DIR = Path("/tmp/cyberquest/backups")  # noqa: F405

# Ready-made demo database copied to /tmp on start (built by scripts/vercel_build.py).
VERCEL_SEED_DB = BASE_DIR / "vercel_seed" / "cyberquest.sqlite3"  # noqa: F405
