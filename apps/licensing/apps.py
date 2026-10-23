"""apps.py - Django app config for Licences and Level Packs. Owner: Rajneesh Kumar."""

from django.apps import AppConfig


class LicensingConfig(AppConfig):
    """Registers the licensing app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.licensing"
    verbose_name = "Licences and Level Packs"
