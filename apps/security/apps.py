"""apps.py - Django app config for Security log. Owner: Anish Shrestha."""
from django.apps import AppConfig


class SecurityConfig(AppConfig):
    """Registers the security app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.security"
    verbose_name = "Security log"
