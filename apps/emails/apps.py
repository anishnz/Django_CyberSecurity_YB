"""apps.py - Django app config for Email. Owner: Rajneesh Kumar."""
from django.apps import AppConfig


class EmailsConfig(AppConfig):
    """Registers the emails app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.emails"
    verbose_name = "Email"
