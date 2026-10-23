"""WSGI entry point used by waitress (Docker and run_local.bat)."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cyberquest.settings.dev")
application = get_wsgi_application()
