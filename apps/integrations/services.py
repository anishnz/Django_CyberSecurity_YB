"""
services.py - Save, test and use integrations (Factory + Adapter)
=================================================================

Owner: Jihe Qi (tasks J-09, J-10)
"""

from __future__ import annotations

from django.utils import timezone

from apps.core.exceptions import NotFoundError, ValidationError
from apps.core.models import FeatureSwitch
from apps.core.services import AuditService
from apps.security.services import SecurityLog

from .adapters import ADAPTERS, AI_ORDER, Adapter, AIProvider, OfflineTemplateProvider
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

    def ai(self) -> AIProvider:
        """The first switched-on AI provider, or the offline helper."""
        if FeatureSwitch.is_on("ai"):
            for name in AI_ORDER:
                if self.enabled(name):
                    return self.adapter(name)
        return OfflineTemplateProvider()

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
