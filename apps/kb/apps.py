"""apps.py - Knowledge Base app (Jihe Qi): pages and a JSON proxy to the RAG service."""

from django.apps import AppConfig


class KbConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.kb'
