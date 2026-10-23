"""
services.py - Save questions written by teachers, the Super Admin or approved AI drafts
======================================================================================

Owner: Anish Shrestha (task A-12)
"""

from __future__ import annotations

from django.db import transaction

from apps.core.exceptions import AccessDeniedError
from apps.core.services import AuditService

from .factory import QuestionFactory
from .models import AnswerOption, Level, Question


class QuestionService:
    """Create, edit and archive questions."""

    @transaction.atomic
    def save(self, data: dict, q_type: str, user, instance: Question | None = None) -> Question:
        """Check the question with QuestionFactory and save it with its answers."""
        domain = QuestionFactory.create(q_type, data)  # raises ValidationError on bad data
        is_teacher = user.is_teacher
        if instance is not None and is_teacher and instance.created_by_id != user.pk:
            raise AccessDeniedError("You can only edit your own questions.")
        row = instance or Question()
        row.level = Level.objects.get(number=data["level"])
        row.category, row.q_type, row.text = data["category"], q_type, domain.text
        row.scenario_text, row.feedback = domain.scenario_text, domain.feedback
        if instance is None and is_teacher:
            row.created_by, row.school = user, user.school
        row.save()
        row.options.all().delete()
        AnswerOption.objects.bulk_create(
            [AnswerOption(question=row, label=o.label, text=o.text, is_correct=o.is_correct) for o in domain.options]
        )
        AuditService.log(user, "question_saved", row.code or f"Q{row.pk}")
        return row

    @staticmethod
    def archive(question: Question, user) -> None:
        """Hide a question (it stays in old results)."""
        if user.is_teacher and question.created_by_id != user.pk:
            raise AccessDeniedError("You can only remove your own questions.")
        question.is_archived = True
        question.save(update_fields=["is_archived"])
        AuditService.log(user, "question_archived", question.code or f"Q{question.pk}")
