"""
factory.py - QuestionFactory (Factory pattern)
==============================================

Owner: Anish Shrestha (task A-13)

One place decides WHICH question class to build from a type name such as
"multi_select". Adding a new type = one new class + one line in ``_TYPES``
(Open/Closed principle). ``validate()`` checks the rules every question must
follow (used by the JSON importer, the teacher form and AI drafts).
"""
from __future__ import annotations

from apps.core.exceptions import ValidationError

from .questions import (MARKS_PER_QUESTION, VALID_LABELS, MultiSelectQuestion, Option, QuestionBase,
                        ScenarioQuestion, SingleChoiceQuestion, TrueFalseQuestion)


class QuestionFactory:
    """Creates the right Question object for a type name."""

    _TYPES: dict[str, type[QuestionBase]] = {
        "single": SingleChoiceQuestion,
        "true_false": TrueFalseQuestion,
        "multi_select": MultiSelectQuestion,
        "scenario": ScenarioQuestion,
    }

    @classmethod
    def types(cls) -> dict[str, str]:
        return {name: klass.TYPE_LABEL for name, klass in cls._TYPES.items()}

    @classmethod
    def klass_for(cls, q_type: str) -> type[QuestionBase]:
        try:
            return cls._TYPES[q_type]
        except KeyError as exc:
            raise ValidationError(f"Unknown question type '{q_type}'. Use one of: {', '.join(cls._TYPES)}.") from exc

    @classmethod
    def create(cls, q_type: str, data: dict) -> QuestionBase:
        """Build from a dictionary (JSON bank, teacher form or AI draft).

        data["options"] = {"A": "text", ...}; data["answer"] = "B" or ["A", "C"]."""
        klass = cls.klass_for(q_type)
        answer = data.get("answer")
        correct = {answer.upper()} if isinstance(answer, str) else {a.upper() for a in (answer or [])}
        options = [Option(label, text, label in correct) for label, text in sorted((data.get("options") or {}).items())]
        question = klass(code=data.get("id"), level_number=data.get("level"), category=data.get("category", ""),
                         text=data.get("text", ""), options=options, feedback=data.get("feedback", ""),
                         marks=data.get("marks", MARKS_PER_QUESTION), topic_code=data.get("topic", ""),
                         scenario_text=data.get("scenario_text", ""), nz_context=bool(data.get("nz_context")),
                         created_by=data.get("created_by"), school_id=data.get("school_id"))
        cls.validate(question)
        return question

    @classmethod
    def from_model(cls, row) -> QuestionBase:
        """Build from a Django Question row and its options."""
        klass = cls.klass_for(row.q_type)
        options = [Option(o.label, o.text, o.is_correct) for o in row.options.all()]
        return klass(pk=row.pk, code=row.code, level_number=row.level.number, category=row.category, text=row.text,
                     options=options, feedback=row.feedback, marks=row.marks, topic_code=row.topic_code,
                     scenario_text=row.scenario_text, nz_context=row.nz_context, created_by=row.created_by_id,
                     school_id=row.school_id)

    @staticmethod
    def validate(q: QuestionBase) -> None:
        """Rules every question must follow."""
        where = f" (question {q.code})" if q.code else ""
        if not q.text or len(q.text.strip()) < 5:
            raise ValidationError(f"Question text is missing or too short{where}.")
        if len(q.text) > 400:
            raise ValidationError(f"Question text must be 400 characters or less{where}.")
        if q.marks != MARKS_PER_QUESTION:
            raise ValidationError(f"Every question must be worth exactly 5 marks{where}.")
        if not q.feedback or len(q.feedback.strip()) < 5:
            raise ValidationError(f"Please write a short feedback explanation{where}.")
        labels = [o.label for o in q.options]
        if not 2 <= len(labels) <= 4:
            raise ValidationError(f"A question needs 2–4 answer options{where}.")
        if any(lbl not in VALID_LABELS for lbl in labels) or len(set(labels)) != len(labels):
            raise ValidationError(f"Option labels must be A, B, C or D with no repeats{where}.")
        if any(not o.text.strip() for o in q.options):
            raise ValidationError(f"Every answer option needs some text{where}.")
        if not q.correct_labels:
            raise ValidationError(f"Please choose the correct answer{where}.")
        if not isinstance(q, MultiSelectQuestion) and len(q.correct_labels) != 1:
            raise ValidationError(f"This question type needs exactly one correct answer{where}.")
        if isinstance(q, TrueFalseQuestion) and labels != ["A", "B"]:
            raise ValidationError(f"True/false questions need exactly options A (True) and B (False){where}.")
        if isinstance(q, ScenarioQuestion) and len(q.scenario_text.strip()) < 10:
            raise ValidationError(f"A scenario question needs a short scenario story{where}.")
