"""apps.py - Django app config for AI assistant. Owner: Jihe Qi."""
from django.apps import AppConfig


class AiAssistantConfig(AppConfig):
    """Registers the ai_assistant app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai_assistant"
    verbose_name = "AI assistant"
