"""
questions.py - Question types as classes (abstraction, inheritance, polymorphism)
==================================================================================

Owner: Anish Shrestha (task A-13)

* ``Question`` is abstract: every type must say how to ``check_answer``.
* SingleChoice, TrueFalse and MultiSelect check differently (polymorphism).
* ScenarioQuestion INHERITS SingleChoiceQuestion's checking – only the display
  is different (a short story before the question).
* Marks are all-or-nothing: 5 marks or 0 (no half marks).

These classes do not know about Django, so they are easy to unit test.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from .categories import category_name

MARKS_PER_QUESTION = 5
VALID_LABELS = ("A", "B", "C", "D")


@dataclass
class Option:
    """One answer choice."""

    label: str
    text: str
    is_correct: bool = False


def normalise_answer(answer) -> list[str]:
    """'b', 'A,C' or ['C','A'] -> sorted unique list like ['A', 'C']."""
    if answer is None:
        return []
    parts = answer.replace(" ", "").split(",") if isinstance(answer, str) else list(answer)
    return sorted({p.strip().upper() for p in parts if p and p.strip()})


class QuestionBase(ABC):
    """Abstract parent for every question type."""

    Q_TYPE = ""
    TYPE_LABEL = ""

    def __init__(self, *, pk=None, code=None, level_number=1, category="", text="", options=(), feedback="",
                 marks=MARKS_PER_QUESTION, topic_code="", scenario_text="", nz_context=False, created_by=None,
                 school_id=None):
        self.pk = pk
        self.code = code
        self.level_number = level_number
        self.category = category
        self.text = text
        self.options: list[Option] = list(options)
        self.feedback = feedback
        self.marks = marks
        self.topic_code = topic_code
        self.scenario_text = scenario_text
        self.nz_context = nz_context
        self.created_by = created_by
        self.school_id = school_id

    @property
    def correct_labels(self) -> list[str]:
        return sorted(o.label for o in self.options if o.is_correct)

    @property
    def correct_text(self) -> str:
        return "; ".join(f"{o.label}. {o.text}" for o in self.options if o.is_correct)

    @property
    def category_name(self) -> str:
        return category_name(self.category, self.level_number)

    @property
    def allows_many(self) -> bool:
        """Screens show checkboxes when True, radio buttons when False."""
        return False

    @property
    def is_teacher_question(self) -> bool:
        return self.created_by is not None

    def option_text(self, label: str) -> str:
        return next((o.text for o in self.options if o.label == label), "")

    def marks_for(self, answer) -> int:
        """All marks or nothing."""
        return self.marks if self.check_answer(answer) else 0

    @abstractmethod
    def check_answer(self, answer) -> bool:
        """True if the answer is right."""

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.code or self.pk}>"


class SingleChoiceQuestion(QuestionBase):
    """Exactly one correct option."""

    Q_TYPE, TYPE_LABEL = "single", "Single choice"

    def check_answer(self, answer) -> bool:
        chosen = normalise_answer(answer)
        return len(chosen) == 1 and chosen == self.correct_labels


class TrueFalseQuestion(QuestionBase):
    """A statement: A = True, B = False."""

    Q_TYPE, TYPE_LABEL = "true_false", "True or false"

    def check_answer(self, answer) -> bool:
        chosen = normalise_answer(answer)
        return len(chosen) == 1 and chosen[0] in ("A", "B") and chosen == self.correct_labels


class MultiSelectQuestion(QuestionBase):
    """Choose ALL correct options; one missing or one extra = 0 marks."""

    Q_TYPE, TYPE_LABEL = "multi_select", "Choose all that apply"

    @property
    def allows_many(self) -> bool:
        return True

    def check_answer(self, answer) -> bool:
        return normalise_answer(answer) == self.correct_labels


class ScenarioQuestion(SingleChoiceQuestion):
    """A short real-life story, then a single-choice question (inherits the checking)."""

    Q_TYPE, TYPE_LABEL = "scenario", "Scenario"
