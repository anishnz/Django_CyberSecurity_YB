"""prod.py - Settings used inside Docker (debug off, secure cookies when HTTPS is on)."""

from .base import *  # noqa: F401,F403  # pylint: disable=wildcard-import,unused-wildcard-import
from .base import env, env_bool

DEBUG = False
SESSION_COOKIE_SECURE = env_bool("HTTPS", False)
CSRF_COOKIE_SECURE = env_bool("HTTPS", False)
if not env("DJANGO_SECRET_KEY"):
    raise RuntimeError("DJANGO_SECRET_KEY must be set in .env for production (run.bat creates it).")
