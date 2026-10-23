"""
progression.py - Which levels a student may open; badges; level up
===================================================================

Owner: Anish Shrestha (task A-15)

Rule: a student moves up when (a) their best exam at the current level is at
least the pass mark AND (b) the school owns the next Level Pack. Level 1 is free.
"""
from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Max

from apps.core.models import SystemSettings
from apps.learning.models import Level
from apps.licensing.services import LevelPackService

from .models import Badge, QuizSession

LEVEL_BADGES = {1: ("Cyber Starter", "star"), 2: ("Cyber Explorer", "compass"), 3: ("Cyber Defender", "shield-shaded"),
                4: ("Cyber Guardian", "shield-lock"), 5: ("Cyber Senior", "mortarboard"), 6: ("Cyber Pro", "gem")}
PERFECT_BADGE = ("Perfect Score", "stars")


@dataclass
class LevelStatus:
    """What a student can do at one level (draws the level trail)."""

    PASSED, OPEN, NEED_PASS, NEED_PACK = "passed", "open", "need_pass", "need_pack"
    level: Level
    status: str
    best: float | None = None
    current: bool = False

    @property
    def is_open(self) -> bool:
        return self.status in (self.PASSED, self.OPEN)

    @property
    def label(self) -> str:
        return {self.PASSED: "Passed", self.OPEN: "Open", self.NEED_PASS: "Locked – pass the level before",
                self.NEED_PACK: "Ask your teacher about this level"}[self.status]


class LevelProgressionService:
    """Level statuses, access checks and what happens after an exam."""

    def __init__(self, packs: LevelPackService | None = None):
        self.packs = packs or LevelPackService()

    @staticmethod
    def passed_levels(student) -> set[int]:
        return set(QuizSession.objects.filter(student=student, mode="exam", passed=True)
                   .values_list("level__number", flat=True))

    @staticmethod
    def best_by_level(student) -> dict[int, float]:
        rows = (QuizSession.objects.filter(student=student, mode="exam", status="finished")
                .values("level__number").annotate(best=Max("percentage")))
        return {r["level__number"]: r["best"] for r in rows}

    def statuses(self, student) -> list[LevelStatus]:
        passed, best = self.passed_levels(student), self.best_by_level(student)
        owned = self.packs.owned_levels(student.school)
        result = []
        for level in Level.objects.all():
            n = level.number
            if n in passed:
                status = LevelStatus.PASSED
            elif n == 1:
                status = LevelStatus.OPEN
            elif (n - 1) not in passed:
                status = LevelStatus.NEED_PASS
            elif n not in owned:
                status = LevelStatus.NEED_PACK
            else:
                status = LevelStatus.OPEN
            result.append(LevelStatus(level, status, best.get(n)))
        open_levels = [s for s in result if s.is_open]
        if open_levels:
            open_levels[-1].current = True
        return result

    def can_access(self, student, level_number: int) -> bool:
        if level_number == 1:
            return True
        passed = self.passed_levels(student)
        return level_number in passed or ((level_number - 1) in passed and self.packs.has_pack(student.school, level_number))

    def current_level(self, student) -> int:
        opened = [s.level.number for s in self.statuses(student) if s.is_open]
        return max(opened) if opened else 1

    def after_exam(self, student, level_number: int, passed: bool, percentage: float) -> dict:
        """Give badges, open the next level when allowed, update current_level."""
        from apps.notifications.services import notify  # pylint: disable=import-outside-toplevel
        result = {"badges": [], "unlocked_level": None, "next_level_needs_pack": False, "next_level": None}
        if passed:
            name, icon = LEVEL_BADGES[level_number]
            _, first_pass = Badge.objects.get_or_create(student=student, name=name, defaults={"icon": icon})
            if first_pass:
                result["badges"].append((name, icon))
            if percentage >= 100:
                _, new = Badge.objects.get_or_create(student=student, name=PERFECT_BADGE[0],
                                                     defaults={"icon": PERFECT_BADGE[1]})
                if new:
                    result["badges"].append(PERFECT_BADGE)
            nxt = level_number + 1
            if nxt <= 6:
                result["next_level"] = nxt
                if self.packs.has_pack(student.school, nxt):
                    result["unlocked_level"] = nxt
                    if first_pass:
                        notify("level_unlocked", {"student_id": student.pk, "level": nxt,
                                                  "level_name": Level.objects.get(number=nxt).name})
                else:
                    result["next_level_needs_pack"] = True
        profile = getattr(student, "student_profile", None)
        if profile is not None:
            profile.current_level = self.current_level(student)
            profile.save(update_fields=["current_level"])
        return result

    @staticmethod
    def pass_mark() -> int:
        return SystemSettings.load().exam_pass_mark
