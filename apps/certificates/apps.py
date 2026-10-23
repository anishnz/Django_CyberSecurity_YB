"""apps.py - Django app config for Certificates. Owner: Dinesh Upreti."""
from django.apps import AppConfig


class CertificatesConfig(AppConfig):
    """Registers the certificates app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.certificates"
    verbose_name = "Certificates"
