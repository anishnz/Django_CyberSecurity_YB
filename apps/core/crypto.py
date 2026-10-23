"""
crypto.py - Encrypt and decrypt secrets stored in the database
==============================================================

Owner: Jihe Qi (key vault, task J-09) - used by integrations and MFA secrets.

Concepts:
    * Fernet (from the ``cryptography`` package) = AES encryption + a check that
      nobody changed the text. If FIELD_ENCRYPTION_KEY is not set, a key is made
      from SECRET_KEY so the app still works on a laptop.
    * ``mask()`` shows only the last 4 characters on screen, e.g. ``••••••7f2a``.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _fernet() -> Fernet:
    """Build the Fernet object from the configured key."""
    key = settings.FIELD_ENCRYPTION_KEY
    if not key:
        digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(digest).decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt(plain: str) -> str:
    """Encrypt text. Empty text stays empty."""
    if not plain:
        return ""
    return _fernet().encrypt(plain.encode()).decode()


def decrypt(token: str) -> str:
    """Decrypt text. Returns '' when the token is empty or was made with another key."""
    if not token:
        return ""
    try:
        return _fernet().decrypt(token.encode()).decode()
    except (InvalidToken, ValueError):
        return ""


def mask(secret: str, show: int = 4) -> str:
    """Hide a secret on screen: '••••••' + last 4 characters."""
    if not secret:
        return ""
    return "••••••" + secret[-show:] if len(secret) > show else "••••"
