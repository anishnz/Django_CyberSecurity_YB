"""
modes.py - Practice and exam modes (Strategy pattern)
=====================================================

Owner: Anish Shrestha (task A-14)

The quiz service asks the mode object what to do after each answer and whether
the result counts for levelling up. Adding a new mode = one new class.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from .feedback import FeedbackService


class QuizMode(ABC):
    """Interface for the ways a quiz can run."""

    name = ""
    label = ""

    @abstractmethod
    def after_answer(self, question, is_correct: bool) -> dict | None:
        """Feedback to show now, or None if feedback waits until the end."""

    @abstractmethod
    def counts_for_level(self) -> bool:
        """True if the result can unlock the next level."""


class PracticeMode(QuizMode):
    """Learn as you go: instant feedback; does not count for levels."""

    name, label = "practice", "Practice quiz"

    def __init__(self, feedback: FeedbackService | None = None):
        self.feedback = feedback or FeedbackService()

    def after_answer(self, question, is_correct):
        return {"is_correct": is_correct, "headline": self.feedback.answer_message(is_correct),
                "explanation": question.feedback, "correct_answer": question.correct_text}

    def counts_for_level(self):
        return False


class ExamMode(QuizMode):
    """Level exam: 20 × 5 marks; feedback only at the end."""

    name, label = "exam", "Level exam"

    def after_answer(self, question, is_correct):
        return None

    def counts_for_level(self):
        return True


MODES = {PracticeMode.name: PracticeMode, ExamMode.name: ExamMode}


def mode_for(name: str) -> QuizMode:
    """Factory for mode objects."""
    return MODES[name]()
