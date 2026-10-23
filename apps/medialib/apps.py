"""apps.py - Django app config for Media library. Owner: Jihe Qi."""

from django.apps import AppConfig


class MedialibConfig(AppConfig):
    """Registers the medialib app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.medialib"
    verbose_name = "Media library"
