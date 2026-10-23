"""dev.py - Settings for a developer laptop (debug on, SQLite)."""
from .base import *  # noqa: F401,F403  (settings files import everything on purpose)

DEBUG = True
STORAGES = {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
            "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}
