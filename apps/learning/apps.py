"""apps.py - Django app config for Learning content. Owner: Anish Shrestha."""
from django.apps import AppConfig


class LearningConfig(AppConfig):
    """Registers the learning app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.learning"
    verbose_name = "Learning content"
