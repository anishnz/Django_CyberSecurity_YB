"""apps.py - Django app config for Integrations and key vault. Owner: Jihe Qi."""

from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    """Registers the integrations app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.integrations"
    verbose_name = "Integrations and key vault"
