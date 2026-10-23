"""
scoring.py - Marks, percentage and awareness level
==================================================

Owner: Anish Shrestha (task A-15)
Awareness bands: Excellent ≥ 90, Good ≥ 75, Developing ≥ 50, otherwise
"Needs more practice" – the app never shows "Fail".
"""

from __future__ import annotations

AWARENESS_BANDS = [
    (90, "Excellent", "success"),
    (75, "Good", "success"),
    (50, "Developing", "warning"),
    (0, "Needs more practice", "info"),
]


class ScoringService:
    """Static helpers grouped in one class."""

    @staticmethod
    def percentage(score: int, max_score: int) -> float:
        return 0.0 if not max_score else round(score * 100 / max_score, 1)

    @staticmethod
    def awareness_level(percentage: float) -> str:
        return next(label for limit, label, _ in AWARENESS_BANDS if percentage >= limit)

    @staticmethod
    def awareness_colour(label: str) -> str:
        return next((c for _, lbl, c in AWARENESS_BANDS if lbl == label), "secondary")

    @staticmethod
    def has_passed(percentage: float, pass_mark: int) -> bool:
        return percentage >= pass_mark
