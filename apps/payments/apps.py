"""apps.py - Django app config for Payments (payslip approval). Owner: Rajneesh Kumar."""
from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    """Registers the payments app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.payments"
    verbose_name = "Payments (payslip approval)"
