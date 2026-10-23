"""
importer.py - Import study topics and question banks from JSON
==============================================================

Owner: Jihe Qi (task J-13)

* Each question is checked with QuestionFactory.validate() before it is saved.
* A question whose category is not one of its level's 4 categories is rejected.
* Importing twice adds nothing new (questions are matched by their code).
"""
from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.db import transaction

from apps.core.exceptions import ValidationError

from .categories import LEVEL_CATEGORIES
from .factory import QuestionFactory
from .models import AnswerOption, LearningTopic, Level, Question

DATA_DIR = Path(settings.BASE_DIR) / "data"


class ContentImporter:
    """Loads levels, topics and questions into the database."""

    @transaction.atomic
    def import_levels_and_topics(self, path: Path | None = None) -> tuple[int, int]:
        data = json.loads(Path(path or DATA_DIR / "learning_topics.json").read_text(encoding="utf-8"))
        for row in data["levels"]:
            Level.objects.update_or_create(number=row["number"], defaults={
                "name": row["name"], "audience": row["audience"], "is_free": row["is_free"],
                "icon": row["icon"], "description": row["description"]})
        levels = {lvl.number: lvl for lvl in Level.objects.all()}
        for row in data["topics"]:
            habits = row.get("habits", "")
            LearningTopic.objects.update_or_create(code=row["code"], defaults={
                "level": levels[row["level"]], "category": row["category"], "title": row["title"],
                "summary": row.get("summary", ""), "body": row["body"],
                "habits": "\n".join(habits) if isinstance(habits, list) else habits,
                "kiwi_example": row.get("kiwi_example", ""), "minutes": row.get("minutes", 3),
                "sort_order": row.get("order", 0)})
        return len(data["levels"]), len(data["topics"])

    @staticmethod
    def validate_file(path: Path) -> list[tuple[dict, object]]:
        """Check every question in one file; return (raw, question) pairs."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        level = data["level"]
        checked = []
        for raw in data["questions"]:
            if raw.get("category") not in LEVEL_CATEGORIES.get(level, []):
                raise ValidationError(f"Question {raw.get('id')}: category {raw.get('category')} is not used in Level {level}.")
            if raw.get("answer") in (None, "", []):
                raise ValidationError(f"Question {raw.get('id')}: the answer is missing.")
            checked.append((raw, QuestionFactory.create(raw.get("q_type", "single"), {**raw, "level": level})))
        return checked

    @transaction.atomic
    def import_file(self, path: Path) -> int:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        level = Level.objects.get(number=data["level"])
        added = 0
        for raw, q in self.validate_file(path):
            if Question.objects.filter(code=q.code).exists():
                continue
            row = Question.objects.create(code=q.code, level=level, category=q.category, q_type=raw.get("q_type", "single"),
                                          topic_code=q.topic_code, text=q.text, scenario_text=q.scenario_text,
                                          feedback=q.feedback, nz_context=q.nz_context)
            AnswerOption.objects.bulk_create([AnswerOption(question=row, label=o.label, text=o.text, is_correct=o.is_correct)
                                              for o in q.options])
            added += 1
        return added

    def import_all(self) -> dict:
        levels, topics = self.import_levels_and_topics()
        questions = sum(self.import_file(p) for p in sorted((DATA_DIR / "question_bank").glob("level*.json")))
        return {"levels": levels, "topics": topics, "questions_added": questions}
