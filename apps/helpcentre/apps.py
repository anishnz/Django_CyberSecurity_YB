"""apps.py - Django app config for Help centre. Owner: Dinesh Upreti."""

from django.apps import AppConfig


class HelpcentreConfig(AppConfig):
    """Registers the helpcentre app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.helpcentre"
    verbose_name = "Help centre"
