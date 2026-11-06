"""
wsgi_vercel.py - WSGI entry point for the online demo on Vercel
===============================================================

Owner: Anish Shrestha (Lead Software Engineer)

Before Django answers the first request, this file makes sure the demo
database exists in /tmp (the only folder Vercel lets us write to):

1. If the build made a ready demo database (vercel_seed/), copy it to /tmp. Fast.
2. Otherwise, create the tables and load the demo data in /tmp. Slower, but safe.

Each new Vercel instance starts again from the same demo data.
"""

import os
import shutil
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cyberquest.settings.vercel")

import django  # noqa: E402  # pylint: disable=wrong-import-position

django.setup()

from django.conf import settings  # noqa: E402  # pylint: disable=wrong-import-position
from django.core.management import call_command  # noqa: E402  # pylint: disable=wrong-import-position
from django.core.wsgi import get_wsgi_application  # noqa: E402  # pylint: disable=wrong-import-position


def prepare_database() -> None:
    """Copy the build's demo database to /tmp, or build one there if it is missing."""
    target = Path(settings.DATABASES["default"]["NAME"])
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)
    seed = Path(getattr(settings, "VERCEL_SEED_DB", ""))
    if seed.is_file():
        shutil.copyfile(seed, target)
        call_command("migrate", interactive=False, verbosity=0)  # quick no-op unless the seed is older
    else:
        call_command("migrate", interactive=False, verbosity=0)
        call_command("seed_demo")


prepare_database()
application = get_wsgi_application()
