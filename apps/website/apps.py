"""apps.py - Django app config for Public website. Owner: Dinesh Upreti."""

from django.apps import AppConfig


class WebsiteConfig(AppConfig):
    """Registers the website app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.website"
    verbose_name = "Public website"
