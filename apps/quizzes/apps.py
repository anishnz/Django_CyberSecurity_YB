"""apps.py - Django app config for Quizzes and exams. Owner: Anish Shrestha."""
from django.apps import AppConfig


class QuizzesConfig(AppConfig):
    """Registers the quizzes app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.quizzes"
    verbose_name = "Quizzes and exams"

    def ready(self) -> None:
        """Connect signal receivers when Django starts."""
        from . import signals  # noqa: F401  pylint: disable=import-outside-toplevel,unused-import

