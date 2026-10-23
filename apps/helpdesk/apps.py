"""apps.py - Django app config for Help desk tickets. Owner: Rajneesh Kumar (backend), Dinesh Upreti (screens)."""
from django.apps import AppConfig


class HelpdeskConfig(AppConfig):
    """Registers the helpdesk app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.helpdesk"
    verbose_name = "Help desk tickets"
