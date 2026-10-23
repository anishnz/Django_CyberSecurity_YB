"""apps.py - Django app config for Announcements (Pānui). Owner: Dinesh Upreti."""

from django.apps import AppConfig


class AnnouncementsConfig(AppConfig):
    """Registers the announcements app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.announcements"
    verbose_name = "Announcements (Pānui)"
