"""prod.py - Settings used inside Docker (debug off, secure cookies when HTTPS is on)."""

from .base import *  # noqa: F401,F403  # pylint: disable=wildcard-import,unused-wildcard-import
from .base import env, env_bool

DEBUG = False
# Local school laptops use http://localhost, so HTTPS features switch on only when HTTPS=1
# (for example behind a reverse proxy with a certificate). check --deploy then only notes HSTS subdomains and
# preload, which are left off on purpose because we do not control every subdomain of a school domain.
HTTPS = env_bool("HTTPS", False)
SESSION_COOKIE_SECURE = HTTPS
CSRF_COOKIE_SECURE = HTTPS
if HTTPS:
    SECURE_SSL_REDIRECT = True
    SECURE_REDIRECT_EXEMPT = [r"^health/$"]  # Docker health check runs inside the container over HTTP
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = int(env("HSTS_SECONDS", "31536000"))
if not env("DJANGO_SECRET_KEY"):
    raise RuntimeError("DJANGO_SECRET_KEY must be set in .env for production (run.bat creates it).")
