"""apps.py - Django app config for Reports and business intelligence. Owner: Dinesh Upreti."""
from django.apps import AppConfig


class ReportsConfig(AppConfig):
    """Registers the reports app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reports"
    verbose_name = "Reports and business intelligence"
