"""apps.py - Django app config for Notifications. Owner: Rajneesh Kumar."""
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Registers the notifications app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
    verbose_name = "Notifications"

    def ready(self) -> None:
        """Connect signal receivers when Django starts."""
        from . import signals  # noqa: F401  pylint: disable=import-outside-toplevel,unused-import

