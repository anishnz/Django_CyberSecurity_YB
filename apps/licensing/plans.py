"""
plans.py - Subscription plans as classes (inheritance + polymorphism)
=====================================================================

Owner: Rajneesh Kumar (task R-05)

Concepts:
    * Abstraction: ``Plan`` is abstract; every plan must answer ``is_active(today)``.
    * Inheritance: TrialPlan, BasicPlan, StandardPlan, UnlimitedPlan share the
      helper methods and only change their class attributes and rule.
    * Polymorphism: ``plan.is_active(today)`` works for any plan; Unlimited is
      always active, Basic/Standard allow 7 grace days, Trial has none.
    * Factory: ``plan_for(code, ...)`` returns the right class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, timedelta
from decimal import Decimal

UNLIMITED_EXPIRY = date(9999, 12, 31)


class Plan(ABC):
    """Abstract parent class for all plans."""

    CODE = ""
    DISPLAY_NAME = ""
    MAX_SECTIONS: int | None = None  # None = no limit
    MONTHLY_PRICE = Decimal("0")  # NZD per school per month
    GRACE_DAYS = 0

    def __init__(self, start_date: date, expiry_date: date, community_discount: bool = False):
        self.start_date = start_date
        self.expiry_date = expiry_date
        self.community_discount = community_discount

    @abstractmethod
    def is_active(self, today: date) -> bool:
        """True if the school may use CyberQuest on this day."""

    def days_left(self, today: date) -> int | None:
        """Days until expiry (negative when expired). None when it never expires."""
        if self.expiry_date >= UNLIMITED_EXPIRY:
            return None
        return (self.expiry_date - today).days

    def in_grace_period(self, today: date) -> bool:
        """Expiry date passed but grace days still running."""
        return self.expiry_date < today <= self.expiry_date + timedelta(days=self.GRACE_DAYS)

    def can_add_section(self, current_sections: int) -> bool:
        return self.MAX_SECTIONS is None or current_sections < self.MAX_SECTIONS

    def monthly_price(self) -> Decimal:
        """Price after the 50% community discount (kura and small rural schools)."""
        return self.MONTHLY_PRICE * (Decimal("0.5") if self.community_discount else 1)

    def status_label(self, today: date) -> str:
        """Text such as 'Active – 10 days left', 'Grace period' or 'Expired'."""
        if not self.is_active(today):
            return "Expired"
        if self.in_grace_period(today):
            return "Grace period"
        left = self.days_left(today)
        if left is None:
            return "Never expires"
        return f"Active – {left} day{'s' if left != 1 else ''} left"

    @property
    def section_limit_label(self) -> str:
        return "Unlimited" if self.MAX_SECTIONS is None else str(self.MAX_SECTIONS)


class TrialPlan(Plan):
    """Free 30-day trial with one section."""

    CODE, DISPLAY_NAME, MAX_SECTIONS, MONTHLY_PRICE = "TRIAL", "Free Trial", 1, Decimal("0")

    def is_active(self, today: date) -> bool:
        return self.start_date <= today <= self.expiry_date


class BasicPlan(Plan):
    """Basic: NZD $100 per month, up to 5 sections, 7 grace days."""

    CODE, DISPLAY_NAME, MAX_SECTIONS, MONTHLY_PRICE, GRACE_DAYS = "BASIC", "Basic", 5, Decimal("100"), 7

    def is_active(self, today: date) -> bool:
        return today <= self.expiry_date + timedelta(days=self.GRACE_DAYS)


class StandardPlan(Plan):
    """Standard: NZD $250 per month, up to 15 sections, 7 grace days."""

    CODE, DISPLAY_NAME, MAX_SECTIONS, MONTHLY_PRICE, GRACE_DAYS = "STANDARD", "Standard", 15, Decimal("250"), 7

    def is_active(self, today: date) -> bool:
        return today <= self.expiry_date + timedelta(days=self.GRACE_DAYS)


class UnlimitedPlan(Plan):
    """Unlimited: NZD $500 per month, no section limit, never expires."""

    CODE, DISPLAY_NAME, MAX_SECTIONS, MONTHLY_PRICE = "UNLIMITED", "Unlimited", None, Decimal("500")

    def is_active(self, today: date) -> bool:  # pylint: disable=unused-argument
        return True


PLAN_CLASSES = {cls.CODE: cls for cls in (TrialPlan, BasicPlan, StandardPlan, UnlimitedPlan)}
PLAN_CHOICES = [(code, cls.DISPLAY_NAME) for code, cls in PLAN_CLASSES.items()]
LEVEL_PACK_PRICES = {2: Decimal("150"), 3: Decimal("150"), 4: Decimal("150"), 5: Decimal("250"), 6: Decimal("400")}
FREE_LEVEL = 1


def plan_for(code: str, start_date: date, expiry_date: date, community_discount: bool = False) -> Plan:
    """Factory: build the right Plan object."""
    try:
        cls = PLAN_CLASSES[code.upper()]
    except KeyError as exc:
        raise ValueError(f"Unknown plan: {code}") from exc
    return cls(start_date, expiry_date, community_discount)
