"""apps.py - Django app config for the JSON API (for a React front end). Owner: Jihe Qi."""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Registers the API app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.api"
    verbose_name = "JSON API for React"
