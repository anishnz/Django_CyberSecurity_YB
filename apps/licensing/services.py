"""
services.py - Licence and Level Pack rules
==========================================

Owner: Rajneesh Kumar (tasks R-05, R-06)

Uses the Plan classes (plans.py) and the key validator (keys.py). Sends events to
the NotificationCenter (Observer pattern) when something changes.
"""

from __future__ import annotations

from datetime import timedelta

from django.db import transaction

from apps.core.clock import today
from apps.core.exceptions import InvalidLicenseKeyError, LicenseExpiredError, LicenseLimitError
from apps.core.models import SystemSettings
from apps.core.services import AuditService

from .keys import LicenseKeyValidator
from .models import License, LevelPack
from .plans import FREE_LEVEL, LEVEL_PACK_PRICES, UNLIMITED_EXPIRY


def _notify(event: str, data: dict) -> None:
    from apps.notifications.services import notify  # pylint: disable=import-outside-toplevel

    notify(event, data)


class LicenseService:
    """Everything about a school's subscription."""

    def __init__(self, validator: LicenseKeyValidator | None = None):
        self.validator = validator or LicenseKeyValidator()

    @staticmethod
    def get(school) -> License | None:
        return License.objects.filter(school=school).first()

    def is_school_active(self, school) -> bool:
        """True if the school is switched on and its plan is active today."""
        if school is None or not school.is_active:
            return False
        lic = self.get(school)
        return bool(lic and lic.plan_obj.is_active(today()))

    def require_active(self, school) -> None:
        if not self.is_school_active(school):
            raise LicenseExpiredError()

    def check_section_limit(self, school) -> None:
        """Raise LicenseLimitError when the plan allows no more sections."""
        lic = self.get(school)
        if lic is None:
            raise LicenseLimitError("This school has no licence yet.")
        if not lic.plan_obj.can_add_section(school.section_count):
            raise LicenseLimitError(
                f"Your {lic.plan_obj.DISPLAY_NAME} plan allows {lic.plan_obj.section_limit_label} "
                "section(s). Ask about upgrading your plan."
            )

    @transaction.atomic
    def start_trial(self, school, days: int = 30) -> License:
        """Give a new school the free 30-day trial."""
        lic, _ = License.objects.update_or_create(
            school=school,
            defaults={"plan": "TRIAL", "start_date": today(), "expiry_date": today() + timedelta(days=days)},
        )
        return lic

    @transaction.atomic
    def set_plan(self, school, plan: str, expiry, by=None, key: str = "") -> License:
        """Change the plan (used by product keys and approved payments)."""
        old = self.get(school)
        lic, _ = License.objects.update_or_create(
            school=school,
            defaults={
                "plan": plan,
                "start_date": today(),
                "expiry_date": expiry or UNLIMITED_EXPIRY,
                "product_key": key,
                "last_warning_sent": None,
            },
        )
        AuditService.log(
            by, "license_updated", school.code, old.plan if old else "-", f"{plan} until {lic.expiry_date}"
        )
        _notify(
            "license_updated",
            {"school_id": school.pk, "plan": lic.get_plan_display(), "expiry": lic.expiry_date.strftime("%d %b %Y")},
        )
        return lic

    def apply_product_key(self, school, key: str, by=None) -> License:
        """Check a product key and update the plan."""
        try:
            info = self.validator.validate_for_school(key, school.code, today())
        except InvalidLicenseKeyError as exc:
            AuditService.log(by, "license_key_rejected", school.code, details=exc.message)
            raise
        return self.set_plan(school, info.plan, info.expiry, by, info.key)

    @staticmethod
    def set_discount(school, on: bool, by=None) -> License:
        """Turn the 50% community discount on or off."""
        lic = License.objects.get(school=school)
        AuditService.log(by, "discount_changed", school.code, lic.community_discount, on)
        lic.community_discount = on
        lic.save(update_fields=["community_discount"])
        return lic

    def expiry_warnings(self) -> int:
        """Send 'licence expiring' once a day per school (fixes the repeat bug from v1)."""
        warn_days = SystemSettings.load().license_warning_days
        sent = 0
        for lic in License.objects.select_related("school").exclude(plan="UNLIMITED"):
            left = lic.plan_obj.days_left(today())
            if left is not None and 0 <= left <= warn_days and lic.last_warning_sent != today():
                lic.last_warning_sent = today()
                lic.save(update_fields=["last_warning_sent"])
                _notify(
                    "license_expiring",
                    {"school_id": lic.school_id, "days": left, "expiry": lic.expiry_date.strftime("%d %b %Y")},
                )
                sent += 1
        return sent


class LevelPackService:
    """Which levels a school can use."""

    def __init__(self, validator: LicenseKeyValidator | None = None):
        self.validator = validator or LicenseKeyValidator()

    @staticmethod
    def owned_levels(school) -> set[int]:
        if school is None:
            return {FREE_LEVEL}
        return {FREE_LEVEL, *LevelPack.objects.filter(school=school).values_list("level", flat=True)}

    def has_pack(self, school, level: int) -> bool:
        return level in self.owned_levels(school)

    @staticmethod
    def add_pack(school, level: int, by=None, key: str = "", expiry=None) -> LevelPack:
        """Add a Level Pack to a school (once per level) and tell the school."""
        pack, created = LevelPack.objects.get_or_create(
            school=school, level=level, defaults={"product_key": key, "expiry_date": expiry}
        )
        if created:
            AuditService.log(by, "level_pack_added", school.code, new=f"Level {level}")
            _notify("level_pack_added", {"school_id": school.pk, "level": level})
        return pack

    def apply_pack_key(self, school, key: str, by=None) -> LevelPack:
        info = self.validator.validate_for_school(key, school.code, today(), level_pack=True)
        return self.add_pack(school, info.level, by, info.key, info.expiry)

    def table(self, school) -> list[dict]:
        """Rows for the Level Packs table (admins only – students never see prices)."""
        owned = self.owned_levels(school)
        rows = [{"level": FREE_LEVEL, "price": 0, "owned": True, "free": True}]
        rows += [
            {"level": lvl, "price": price, "owned": lvl in owned, "free": False}
            for lvl, price in LEVEL_PACK_PRICES.items()
        ]
        return rows
