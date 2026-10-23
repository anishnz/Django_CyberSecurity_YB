"""
services.py - Audit log and settings services (overwrite warning)
=================================================================

Owners: Rajneesh Kumar (AuditService, OverwriteWarning, task R-14);
        Anish Shrestha (SettingsService, task A-16)

Concepts:
    * Service layer: views stay thin and call these classes.
    * "Overwrite with warning" (business rule): ``preview_change`` returns
      (old, new) for the confirm page; only ``apply_change`` saves.
    * Every change is written to the AuditLog.
"""

from __future__ import annotations

import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models

from .exceptions import NotFoundError, ValidationError
from .models import AuditLog, SystemSettings

logger = logging.getLogger("cyberquest")


class AuditService:
    """Writes one line to the audit log for every important change."""

    @staticmethod
    def log(user, action: str, target: str = "", old="", new="", details: str = "") -> AuditLog:
        """Save an audit entry and copy it to the log file."""
        username = getattr(user, "username", "") or "system"
        entry = AuditLog.objects.create(
            user=user if getattr(user, "pk", None) else None, username=username, action=action,
            target=str(target)[:200], old_value=str(old), new_value=str(new), details=details)
        logger.info("AUDIT %s by %s: %s %s -> %s %s", action, username, target, old, new, details)
        return entry


class SettingsService:
    """Read and change system settings with an overwrite warning (Super Admin only)."""

    def __init__(self):
        self.settings = SystemSettings.load()

    def rows(self) -> list[dict]:
        """Settings as rows for the settings page."""
        result = []
        for name in SystemSettings.EDITABLE:
            field = SystemSettings._meta.get_field(name)
            result.append({
                "key": name, "label": field.verbose_name.capitalize(), "help": field.help_text,
                "value": getattr(self.settings, name), "is_bool": isinstance(field, models.BooleanField),
                "min": next((v.limit_value for v in field.validators if v.__class__.__name__ == "MinValueValidator"), None),
                "max": next((v.limit_value for v in field.validators if v.__class__.__name__ == "MaxValueValidator"), None),
            })
        return result

    def _convert(self, key: str, raw: str):
        """Turn the typed text into the right type and check the allowed range."""
        if key not in SystemSettings.EDITABLE:
            raise NotFoundError(f"Unknown setting '{key}'.")
        field = SystemSettings._meta.get_field(key)
        if isinstance(field, models.BooleanField):
            value = str(raw).lower() in {"1", "true", "on", "yes"}
        elif isinstance(field, models.PositiveSmallIntegerField):
            try:
                value = int(raw)
            except (TypeError, ValueError) as exc:
                raise ValidationError(f"'{field.verbose_name}' must be a whole number.") from exc
        else:
            value = (raw or "").strip()
        try:
            field.run_validators(value)
            field.clean(value, self.settings)
        except DjangoValidationError as exc:
            raise ValidationError(f"{field.verbose_name.capitalize()}: {' '.join(exc.messages)}") from exc
        return value

    def preview_change(self, key: str, raw: str) -> tuple:
        """Return (old, new) without saving - used for the overwrite warning page."""
        new = self._convert(key, raw)
        return getattr(self.settings, key), new

    def apply_change(self, key: str, raw: str, user) -> tuple:
        """Save the new value, write the audit log and notify Super Admins."""
        old, new = self.preview_change(key, raw)
        setattr(self.settings, key, new)
        self.settings.updated_by = getattr(user, "username", "")
        self.settings.save()
        AuditService.log(user, "settings_change", key, old, new)
        from apps.notifications.services import notify  # pylint: disable=import-outside-toplevel
        notify("settings_changed", {"key": key, "old": old, "new": new, "by": getattr(user, "username", "")})
        return old, new
