"""
base.py - Settings shared by every environment (dev, test, prod)
================================================================

Project : CyberQuest (Django) - Learn. Play. Decide. Stay Cyber Safe.
Code    : YB_student_project_270889991 - MSE800 Assessment 2, Yoobee College
Owner   : Anish Shrestha (Lead Software Engineer)

Why a settings package?
    One base file holds what never changes. dev.py, test.py and prod.py only
    change what is different (debug, database, email backend). This keeps
    secrets out of the code: they are read from environment variables (.env).
"""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _load_dotenv(path: Path) -> None:
    """Read KEY=VALUE lines from .env (made by run.bat) without overriding real environment variables."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_dotenv(BASE_DIR / ".env")


def env(name: str, default: str = "") -> str:
    """Read a setting from the environment (Docker passes .env values in)."""
    return os.environ.get(name, default)


def env_bool(name: str, default: bool = False) -> bool:
    """Read a true/false setting, e.g. DEMO_MODE=1."""
    return env(name, "1" if default else "0").lower() in {"1", "true", "yes", "on"}


# --------------------------------------------------------------- project info
PROJECT = {
    "name": "CyberQuest",
    "tagline": "Learn. Play. Decide. Stay Cyber Safe.",
    "version": "1.0.0",
    "code": "YB_student_project_270889991",
    "company": "Mount Everest Digital Limited",
    "company_address": "5B/2 White Street, Auckland CBD, Auckland 1010",
    "college": "Yoobee College of Creative Innovation",
    "course": "MSE800 Professional Software Engineering - Assessment 2",
    "lecturer": "Dr. Farah Younas",
    "team": [
        ("Anish Shrestha", "270889991", "Lead Software Engineer, system designer, Scrum Master"),
        ("Rajneesh Kumar", "270245010", "Backend and Database Developer"),
        ("Dinesh Upreti", "270830269", "Frontend Developer (UI/UX), Business Analyst"),
        ("Jihe Qi", "27008116", "QA Lead and Integrations Developer"),
    ],
}

# ------------------------------------------------------------------- security
SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-change-me-cyberquest-270889991")
DEBUG = False
ALLOWED_HOSTS = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in env("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

# Key used to encrypt API keys and MFA secrets in the database (Fernet).
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY", "")
# Key used to sign product keys and Level Pack keys (HMAC-SHA256).
LICENSE_SECRET = env("LICENSE_SECRET", "everest-cyberquest-2026")

DEMO_MODE = env_bool("DEMO_MODE", True)

# ----------------------------------------------------------------------- apps
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # CyberQuest apps (owner in brackets)
    "apps.core",  # settings, health, audit, backups (Anish / Rajneesh)
    "apps.accounts",  # users, roles, MFA, Login as (Anish)
    "apps.security",  # security log, lockout (Anish)
    "apps.schools",  # schools, classes, sections, students (Rajneesh)
    "apps.licensing",  # plans, product keys, Level Packs (Rajneesh)
    "apps.payments",  # payslip upload and approval (Rajneesh)
    "apps.learning",  # levels, topics, questions (Anish)
    "apps.quizzes",  # practice, exam, scoring, badges (Anish)
    "apps.notifications",  # Observer pattern, bell (Rajneesh)
    "apps.emails",  # SMTP, IMAP, templates (Rajneesh)
    "apps.helpdesk",  # tickets (Rajneesh backend, Dinesh screens)
    "apps.reports",  # class reports, BI (Dinesh)
    "apps.helpcentre",  # help articles, tour, explain (Dinesh)
    "apps.certificates",  # PDF certificates with QR (Dinesh)
    "apps.announcements",  # Pānui (Dinesh)
    "apps.integrations",  # key vault and adapters (Jihe)
    "apps.ai_assistant",  # AI drafts and text help (Jihe)
    "apps.medialib",  # image, audio, video, YouTube (Jihe)
    "apps.website",  # public website (Dinesh)
    "apps.api",  # JSON API for React + API check page (Jihe)
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.MaintenanceModeMiddleware",
    "apps.accounts.middleware.AccountStatusMiddleware",
    "apps.accounts.middleware.MFARequiredMiddleware",
    "apps.core.middleware.FriendlyErrorMiddleware",
    "apps.core.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "cyberquest.urls"
WSGI_APPLICATION = "cyberquest.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.project",
                "apps.helpcentre.context_processors.page_help",
            ],
        },
    },
]

# ------------------------------------------------------------------- database
# SQLite by default (simple, offline). Set DATABASE_ENGINE=postgres in .env to use PostgreSQL.
if env("DATABASE_ENGINE", "sqlite") == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB", "cyberquest"),
            "USER": env("POSTGRES_USER", "cyberquest"),
            "PASSWORD": env("POSTGRES_PASSWORD", ""),
            "HOST": env("POSTGRES_HOST", "db"),
            "PORT": env("POSTGRES_PORT", "5432"),
        }
    }
else:
    _SQLITE = Path(env("SQLITE_PATH", str(BASE_DIR / "instance" / "cyberquest.sqlite3")))
    _SQLITE.parent.mkdir(parents=True, exist_ok=True)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": _SQLITE,
            "OPTIONS": {"timeout": 20},
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:home"
LOGOUT_REDIRECT_URL = "website:home"

PASSWORD_RESET_TIMEOUT = 3600  # reset links work for 1 hour
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "apps.accounts.validators.LetterAndNumberValidator"},
]

# ---------------------------------------------------------------- language/time
LANGUAGE_CODE = "en-nz"
TIME_ZONE = "Pacific/Auckland"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------- static/media
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_ROOT.mkdir(exist_ok=True)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(env("MEDIA_ROOT", str(BASE_DIR / "media")))

# Upload size limits in megabytes (Super Admin can lower them in System settings).
UPLOAD_LIMITS_MB = {"image": 5, "audio": 20, "video": 100, "document": 10, "payslip": 5, "csv": 2}
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# ------------------------------------------------------------------- sessions
SESSION_COOKIE_AGE = 60 * 60 * 2  # 2 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

# ---------------------------------------------------------------------- email
# Default: emails are written to the console/log. The Super Admin can save Gmail
# SMTP details on the Integrations page; apps.emails then sends through Gmail.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "CyberQuest <no-reply@cyberquest.local>")

# -------------------------------------------------------------------- logging
LOG_DIR = Path(env("LOG_DIR", str(BASE_DIR / "logs")))
LOG_DIR.mkdir(parents=True, exist_ok=True)
# React (or other) front ends on these addresses may call the public, read-only API.
API_CORS_ORIGINS = [
    o.strip() for o in env("API_CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",") if o.strip()
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "cyberquest.log"),
            "maxBytes": 1_000_000,
            "backupCount": 3,
            "formatter": "simple",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "cyberquest": {"handlers": ["console", "file"], "level": "INFO"},
        "django.request": {"handlers": ["file"], "level": "WARNING"},
    },
}

# ---------------------------------------------------------- CyberQuest rules
CYBERQUEST = {
    "LOCKOUT_ATTEMPTS": 5,  # wrong passwords before the account is locked
    "LOCKOUT_MINUTES": 15,
    "SITE_URL": env("SITE_URL", "http://127.0.0.1:8000"),
}
