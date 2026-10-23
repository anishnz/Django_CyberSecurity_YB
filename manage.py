#!/usr/bin/env python
"""manage.py - Django command line (runserver, migrate, seed_demo, import_content ...)."""

import os
import sys


def main() -> None:
    """Run a Django management command."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cyberquest.settings.dev")
    from django.core.management import execute_from_command_line  # pylint: disable=import-outside-toplevel

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
