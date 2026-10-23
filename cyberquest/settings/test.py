"""test.py - Fast settings for pytest (in-memory database, quick password hashing)."""

import tempfile
from pathlib import Path

from .base import *  # noqa: F401,F403  # pylint: disable=wildcard-import,unused-wildcard-import

DEBUG = False
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
MEDIA_ROOT = Path(tempfile.mkdtemp(prefix="cq-media-"))
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
DEMO_MODE = True
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
