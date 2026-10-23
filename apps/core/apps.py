"""apps.py - Django app config for Core (settings, health, audit, backups). Owner: Anish Shrestha / Rajneesh Kumar."""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Registers the core app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core (settings, health, audit, backups)"
