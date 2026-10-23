"""
services.py - NotificationCenter (Observer pattern)
===================================================

Owner: Rajneesh Kumar (task R-08)

Concepts:
    * Observer pattern: NotificationCenter (the subject) keeps a list of observers.
      When something happens (``notify("exam_completed", {...})``) every observer
      gets ``update(event, data)``.
    * DashboardNotifier saves bell messages; LogFileObserver writes the log;
      EmailObserver (apps.emails) sends parent emails. A broken observer never stops
      the others.
    * Singleton-style access: ``center()`` returns the one shared NotificationCenter.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections import defaultdict

from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Notification

logger = logging.getLogger("cyberquest")


class Observer(ABC):
    """Anything that wants to hear about events."""

    @abstractmethod
    def update(self, event: str, data: dict) -> None:
        """React to an event."""


class NotificationCenter:
    """The subject: keeps observers and tells them about events."""

    ALL = "*"

    def __init__(self):
        self._observers: dict[str, list[Observer]] = defaultdict(list)

    def subscribe(self, observer: Observer, event: str = ALL) -> None:
        if observer not in self._observers[event]:
            self._observers[event].append(observer)

    def unsubscribe(self, observer: Observer, event: str = ALL) -> None:
        if observer in self._observers[event]:
            self._observers[event].remove(observer)

    def observer_count(self) -> int:
        return sum(len(v) for v in self._observers.values())

    def notify(self, event: str, data: dict) -> None:
        for observer in self._observers[event] + self._observers[self.ALL]:
            try:
                observer.update(event, data)
            except Exception:  # pylint: disable=broad-except
                logger.exception("Observer %s failed for %s", type(observer).__name__, event)


def _ids(role: str, school_id) -> list[int]:
    users = get_user_model().objects.filter(role=role, school_id=school_id, is_active=True)
    return list(users.values_list("pk", flat=True))


def _super_ids() -> list[int]:
    return list(get_user_model().objects.filter(role="super_admin", is_active=True).values_list("pk", flat=True))


class DashboardNotifier(Observer):
    """Turns events into bell messages (one small method per event)."""

    @staticmethod
    def send(user_ids, message, kind="info", icon="bell", link="", once_per_day=False) -> int:
        """Save a dashboard notice for each user. Returns how many were made."""
        made = 0
        start = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
        for uid in set(user_ids):
            if (
                once_per_day
                and Notification.objects.filter(recipient_id=uid, message=message, created_at__gte=start).exists()
            ):
                continue
            Notification.objects.create(recipient_id=uid, message=message[:300], kind=kind, icon=icon, link=link)
            made += 1
        return made

    def update(self, event, data):
        handler = getattr(self, f"_on_{event}", None)
        if handler:
            handler(data)

    def _on_exam_completed(self, d):
        pct = d["percentage"]
        msg = (
            f"Level {d['level']} exam: {pct:.0f}%. Ka pai! (Well done!)"
            if d["passed"]
            else f"Level {d['level']} exam: {pct:.0f}%. Review the topics and try again – kia kaha! (keep going!)"
        )
        self.send(
            [d["student_id"]], msg, "success" if d["passed"] else "info", "trophy" if d["passed"] else "journal-check"
        )
        self.send(
            d.get("teacher_ids", []),
            f"{d['student_name']} finished the Level {d['level']} exam with {pct:.0f}%.",
            "info",
            "clipboard-check",
        )

    def _on_level_unlocked(self, d):
        self.send([d["student_id"]], f"Level {d['level']} – {d['level_name']} is open for you!", "success", "unlock")

    def _on_level_pack_added(self, d):
        self.send(
            _ids("school_admin", d["school_id"]) + _ids("teacher", d["school_id"]),
            f"Level Pack {d['level']} is now available for your school.",
            "success",
            "box-seam",
        )

    def _on_license_updated(self, d):
        self.send(
            _ids("school_admin", d["school_id"]),
            f"Licence updated: {d['plan']} plan, until {d['expiry']}.",
            "success",
            "patch-check",
        )

    def _on_license_expiring(self, d):
        self.send(
            _ids("school_admin", d["school_id"]),
            f"Licence ends in {d['days']} days ({d['expiry']}). Please arrange a renewal.",
            "warning",
            "exclamation-triangle",
            once_per_day=True,
        )

    def _on_section_full(self, d):
        self.send(
            _ids("school_admin", d["school_id"]), f"Section {d['section']} is full ({d['label']}).", "warning", "people"
        )

    def _on_settings_changed(self, d):
        self.send(
            _super_ids(), f"Setting '{d['key']}' changed from {d['old']} to {d['new']} by {d['by']}.", "info", "gear"
        )

    def _on_exam_assigned(self, d):
        self.send(
            d.get("student_ids", []),
            f"New exam: Level {d['level']}" + (f", due {d['due']}" if d.get("due") else "") + ".",
            "info",
            "calendar-check",
        )

    def _on_payment_submitted(self, d):
        self.send(
            _super_ids(),
            f"New payslip from {d['school']} ({d['item']}, ${d['amount']}). Please review.",
            "info",
            "cash-coin",
            link="/payments/",
        )

    def _on_payment_reviewed(self, d):
        self.send(
            _ids("school_admin", d["school_id"]),
            f"Payment {d['status']}: {d['item']}.",
            "success" if d["status"] == "approved" else "danger",
            "cash-coin",
        )

    def _on_ticket_event(self, d):
        self.send(d.get("user_ids", []), d["message"], "info", "life-preserver", link=d.get("link", ""))

    def _on_demo_reset(self, d):
        self.send(_super_ids(), f"Demo data was reset by {d['by']}.", "warning", "arrow-repeat")


class LogFileObserver(Observer):
    """Writes every event to logs/cyberquest.log (handy when debugging)."""

    def update(self, event, data):
        safe = {k: v for k, v in data.items() if not k.endswith("_ids")}
        logger.info("EVENT %s %s", event, safe)


_CENTER: NotificationCenter | None = None


def center() -> NotificationCenter:
    """The one shared NotificationCenter, created on first use with its observers."""
    global _CENTER  # pylint: disable=global-statement
    if _CENTER is None:
        _CENTER = NotificationCenter()
        _CENTER.subscribe(DashboardNotifier())
        _CENTER.subscribe(LogFileObserver())
    return _CENTER


def notify(event: str, data: dict) -> None:
    """Short helper used everywhere: notify('exam_completed', {...})."""
    center().notify(event, data)


def unread_count(user) -> int:
    return Notification.objects.filter(recipient=user, is_read=False).count() if user.is_authenticated else 0
