"""
vercel_build.py - Build step for the online demo on Vercel
==========================================================

Owner: Anish Shrestha (Lead Software Engineer)

Vercel runs this once per deployment, after it installs requirements.txt
(see [tool.vercel.scripts] in pyproject.toml). It makes a ready demo database
in vercel_seed/ so each new Vercel instance only has to copy one file to /tmp,
instead of creating 43 tables and the demo data on every cold start.
Vercel runs collectstatic by itself, so this script does not.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "vercel_seed" / "cyberquest.sqlite3"


def main() -> None:
    """Create vercel_seed/cyberquest.sqlite3 with all tables and the demo data."""
    sys.path.insert(0, str(ROOT))
    SEED.parent.mkdir(parents=True, exist_ok=True)
    if SEED.exists():
        SEED.unlink()
    os.environ["SQLITE_PATH"] = str(SEED)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cyberquest.settings.vercel")
    os.environ.setdefault("DJANGO_SECRET_KEY", "build-only-not-used-at-runtime")

    import django  # pylint: disable=import-outside-toplevel
    from django.core.management import call_command  # pylint: disable=import-outside-toplevel

    django.setup()
    call_command("migrate", interactive=False, verbosity=1)
    call_command("seed_demo")
    print(f"Demo database ready: {SEED} ({SEED.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
