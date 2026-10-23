"""apps.py - Django app config for Accounts (users, roles, MFA, Login as). Owner: Anish Shrestha."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Registers the accounts app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Accounts (users, roles, MFA, Login as)"

    def ready(self) -> None:
        """Connect signal receivers when Django starts."""
        from . import signals  # noqa: F401  pylint: disable=import-outside-toplevel,unused-import
