"""
services.py - Save, test and use integrations (Factory + Adapter)
=================================================================

Owner: Jihe Qi (tasks J-09, J-10, J-14)

AI models: the Super Admin switches models on, picks a default and sets the order
(Integrations → AI models). ``ai()`` returns a FallbackAIProvider that tries them in
that order and ends with the offline helper, so a teacher always gets a draft.
"""

from __future__ import annotations

import re

from django.utils import timezone

from apps.core.exceptions import NotFoundError, ValidationError
from apps.core.models import FeatureSwitch
from apps.core.services import AuditService
from apps.security.services import SecurityLog

from .adapters import ADAPTERS, AI_ORDER, Adapter, AIProvider, FallbackAIProvider, OfflineTemplateProvider
from .models import IntegrationSetting


class IntegrationService:
    """The single place that builds adapters from saved settings."""

    @staticmethod
    def row(provider: str) -> IntegrationSetting:
        if provider not in ADAPTERS:
            raise NotFoundError(f"Unknown integration '{provider}'.")
        obj, _ = IntegrationSetting.objects.get_or_create(provider=provider)
        return obj

    def adapter(self, provider: str) -> Adapter:
        """Factory: settings row -> adapter object."""
        row = self.row(provider)
        return ADAPTERS[provider](row.get_secret(), row.extra)

    def save(self, provider: str, *, secret: str | None, extra: dict, enabled: bool, user=None, request=None):
        """Save settings; a new key is encrypted and written to the security log."""
        row = self.row(provider)
        cls = ADAPTERS[provider]
        clean_extra = {k: (extra.get(k) or default).strip() for k, _, default in cls.extra_fields}
        if secret:
            if len(secret) > 500:
                raise ValidationError("That key is too long.")
            row.set_secret(secret.strip())
            row.status = "saved"
            SecurityLog.record("api_key_changed", request, user, details=provider)
        row.extra, row.enabled = clean_extra, enabled
        row.save()
        AuditService.log(user, "integration_saved", provider, new="on" if enabled else "off")
        return row

    def clear(self, provider: str, user=None, request=None) -> None:
        row = self.row(provider)
        row.set_secret("")
        row.enabled, row.status, row.last_error = False, "not_set", ""
        row.save()
        SecurityLog.record("api_key_changed", request, user, details=f"{provider} key removed")

    def test(self, provider: str) -> tuple[bool, str]:
        """Run the adapter's connection test and save the result on the card."""
        row = self.row(provider)
        ok, msg = self.adapter(provider).test_connection()
        row.status, row.last_error, row.last_checked = (
            ("connected" if ok else "error"),
            ("" if ok else msg[:300]),
            timezone.now(),
        )
        row.save(update_fields=["status", "last_error", "last_checked"])
        return ok, msg

    def enabled(self, provider: str) -> bool:
        row = IntegrationSetting.objects.filter(provider=provider).first()
        return bool(row and row.enabled and (row.has_secret or not ADAPTERS[provider].needs_secret))

    # ------------------------------------------------------------------ AI models
    @staticmethod
    def _ai_sort_key(row: IntegrationSetting | None, name: str) -> tuple:
        """Default first, then the Super Admin's order number, then the agreed order (Gemini, DeepSeek …)."""
        if row is None:
            return (1, 50, AI_ORDER.index(name))
        return (0 if row.is_default else 1, row.priority, AI_ORDER.index(name))

    def ai_order(self) -> list[str]:
        """Every AI provider name, in the order they will be tried."""
        rows = {r.provider: r for r in IntegrationSetting.objects.filter(provider__in=AI_ORDER)}
        return sorted(AI_ORDER, key=lambda name: self._ai_sort_key(rows.get(name), name))

    def ai(self) -> AIProvider:
        """The AI for drafts: switched-on models in order with automatic fallback, ending with the offline helper."""
        if not FeatureSwitch.is_on("ai"):
            return OfflineTemplateProvider()
        providers = [self.adapter(name) for name in self.ai_order() if self.enabled(name)]
        if not providers:
            return OfflineTemplateProvider()
        return FallbackAIProvider(providers, on_result=self.record_result)

    @staticmethod
    def record_result(provider: str, ok: bool, message: str) -> None:
        """Save what happened on the provider's card (status, last error, time)."""
        IntegrationSetting.objects.filter(provider=provider).update(
            status="connected" if ok else "error",
            last_error="" if ok else message[:300],
            last_checked=timezone.now(),
        )

    def ai_rows(self) -> list[dict]:
        """One row per AI model for the AI models page, in the order they are tried."""
        rows = {r.provider: r for r in IntegrationSetting.objects.filter(provider__in=AI_ORDER)}
        out = []
        for position, name in enumerate(self.ai_order(), start=1):
            row, cls = rows.get(name), ADAPTERS[name]
            out.append(
                {
                    "provider": name,
                    "label": self.adapter(name).label if row else cls.label,
                    "row": row,
                    "position": position,
                    "ready": self.enabled(name),
                    "has_key": bool(row and row.has_secret) or not cls.needs_secret,
                    "model": (row.extra.get("model") if row else "")
                    or dict((k, d) for k, _, d in cls.extra_fields).get("model", ""),
                }
            )
        return out

    def save_ai_settings(self, *, order: dict[str, int], default: str, switched_on: set[str], user=None) -> None:
        """Save the AI order, the default model and which models are on."""
        if default and default not in AI_ORDER:
            raise ValidationError("Unknown AI model.")
        for name in AI_ORDER:
            row = self.row(name)
            number = order.get(name, row.priority)
            if not 1 <= int(number) <= 99:
                raise ValidationError("Order numbers must be between 1 and 99.")
            row.priority = int(number)
            row.is_default = name == default
            row.enabled = name in switched_on
            row.save(update_fields=["priority", "is_default", "enabled", "updated_at"])
        AuditService.log(user, "ai_settings_saved", "ai", new=f"default={default or 'none'}; order={self.ai_order()}")

    # ------------------------------------------------------------------ WhatsApp
    @staticmethod
    def clean_phone(raw: str) -> str:
        """'+64 21 123 4567' -> '64211234567'. International format, 8-15 digits."""
        digits = re.sub(r"[\s\-()]", "", raw or "")
        digits = digits[1:] if digits.startswith("+") else digits
        if not digits.isdigit() or not 8 <= len(digits) <= 15 or digits.startswith("0"):
            raise ValidationError("Use the international format with the country code, for example +64 21 123 4567.")
        return digits

    def whatsapp_test(self, phone: str, *, user=None) -> str:
        """Send Meta's test template to one number. Super Admin only; written to the audit log."""
        to = self.clean_phone(phone)
        message_id = self.adapter("whatsapp").send_template(to)
        AuditService.log(user, "whatsapp_test_sent", "whatsapp", new=f"to …{to[-3:]}")
        return message_id

    def status_summary(self) -> dict[str, str]:
        rows = {r.provider: r for r in IntegrationSetting.objects.all()}
        return {
            name: (rows[name].status if name in rows else "not_set")
            + ("" if name not in rows or rows[name].enabled else " (off)")
            for name in ADAPTERS
            if name not in ("offline", "share")
        }

    def cards(self) -> list[dict]:
        """One card per integration for the Integrations page."""
        out = []
        for name, cls in ADAPTERS.items():
            row = IntegrationSetting.objects.filter(provider=name).first()
            out.append(
                {
                    "provider": name,
                    "cls": cls,
                    "row": row,
                    "extra": [
                        (k, label, (row.extra.get(k) if row and row.extra.get(k) else default))
                        for k, label, default in cls.extra_fields
                    ],
                }
            )
        return out


def map_for(query: str = "", lat=None, lng=None) -> dict:
    """Google Maps for a place: an embedded map when a key is saved, otherwise a free 'Open in Google Maps' link."""
    from urllib.parse import quote_plus  # pylint: disable=import-outside-toplevel

    where = f"{lat},{lng}" if lat is not None and lng is not None else (query or "")
    if not where or not FeatureSwitch.is_on("maps"):
        return {}
    out = {"link": f"https://www.google.com/maps/search/?api=1&query={quote_plus(where)}"}
    service = IntegrationService()
    if service.enabled("google_maps"):
        out["embed"] = service.adapter("google_maps").embed_url(where)
    return out
