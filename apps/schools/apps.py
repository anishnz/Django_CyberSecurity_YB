"""apps.py - Django app config for Schools, classes and sections. Owner: Rajneesh Kumar."""

from django.apps import AppConfig


class SchoolsConfig(AppConfig):
    """Registers the schools app with Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.schools"
    verbose_name = "Schools, classes and sections"
