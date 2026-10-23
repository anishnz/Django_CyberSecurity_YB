"""
models.py - Integration settings (encrypted key vault)
======================================================

Owner: Jihe Qi (task J-09)

One row per outside service. Secrets (API keys, App Passwords, tokens) are
encrypted with Fernet (apps/core/crypto.py) and only shown masked on screen.
"""

from __future__ import annotations

from django.db import models

from apps.core import crypto


class IntegrationSetting(models.Model):
    """Settings for one provider, e.g. 'gmail', 'openai', 'whatsapp'."""

    provider = models.SlugField(max_length=30, unique=True)
    enabled = models.BooleanField(default=False)
    _secret = models.TextField(blank=True, db_column="secret")
    extra = models.JSONField(default=dict, blank=True, help_text="Non-secret settings (address, model, phone id …).")
    status = models.CharField(max_length=20, default="not_set")  # not_set / connected / error
    last_checked = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=300, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.provider} ({self.status})"

    def get_secret(self) -> str:
        return crypto.decrypt(self._secret)

    def set_secret(self, value: str) -> None:
        self._secret = crypto.encrypt(value)

    @property
    def masked(self) -> str:
        return crypto.mask(self.get_secret())

    @property
    def has_secret(self) -> bool:
        return bool(self._secret)
