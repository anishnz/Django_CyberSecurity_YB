"""
models.py - Exam rules, assignments, quiz sessions, answers and badges
======================================================================

Owner: Anish Shrestha (task A-14)

* ExamRules builds a level exam: 20 questions, 5 per category, 5 marks each.
* QuizSession is one attempt (practice or exam). The ordered question ids are
  saved so an unfinished exam can be resumed.
* Response stores each answer once (unique session + question).
"""
from __future__ import annotations

import random

from django.conf import settings
from django.db import models

from apps.core.exceptions import ValidationError


class ExamRules:
    """Rules for building a level exam (plain class – easy to unit test)."""

    def __init__(self, level_number: int, question_count: int = 20, marks_each: int = 5, per_category: int = 5):
        self.level_number = level_number
        self.question_count = question_count
        self.marks_each = marks_each
        self.per_category = per_category

    @property
    def total_marks(self) -> int:
        return self.question_count * self.marks_each

    def build(self, pool: dict[str, list[int]], categories: list[str], rng: random.Random | None = None) -> list[int]:
        """Pick ``per_category`` ids from each category; fill gaps from leftovers; shuffle."""
        rng = rng or random.Random()
        chosen, leftovers = [], []
        for code in categories:
            ids = list(pool.get(code, []))
            rng.shuffle(ids)
            chosen += ids[: self.per_category]
            leftovers += ids[self.per_category:]
        rng.shuffle(leftovers)
        while len(chosen) < self.question_count and leftovers:
            chosen.append(leftovers.pop())
        if len(chosen) < self.question_count:
            raise ValidationError(f"Level {self.level_number} needs {self.question_count} approved questions "
                                  f"but only {len(chosen)} are available.")
        chosen = chosen[: self.question_count]
        rng.shuffle(chosen)
        return chosen


class Assignment(models.Model):
    """A teacher assigns a level exam to a section (with an optional due date)."""

    level = models.ForeignKey("learning.Level", on_delete=models.CASCADE)
    section = models.ForeignKey("schools.Section", on_delete=models.CASCADE, related_name="assignments")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["level__number"]
        constraints = [models.UniqueConstraint(fields=["level", "section"], name="one_assignment_per_level_section")]

    def __str__(self) -> str:
        return f"Level {self.level.number} → {self.section}"


class QuizSession(models.Model):
    """One attempt at a practice quiz or a level exam."""

    PRACTICE, EXAM = "practice", "exam"
    IN_PROGRESS, FINISHED = "in_progress", "finished"

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_sessions")
    level = models.ForeignKey("learning.Level", on_delete=models.CASCADE)
    mode = models.CharField(max_length=10, choices=[(PRACTICE, "Practice"), (EXAM, "Exam")])
    category = models.CharField(max_length=10, blank=True)
    question_ids = models.JSONField(default=list)
    status = models.CharField(max_length=12, default=IN_PROGRESS,
                              choices=[(IN_PROGRESS, "In progress"), (FINISHED, "Finished")])
    score = models.PositiveSmallIntegerField(default=0)
    max_score = models.PositiveSmallIntegerField(default=0)
    percentage = models.FloatField(default=0)
    awareness_level = models.CharField(max_length=30, blank=True)
    passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [models.Index(fields=["student", "mode", "status"])]

    def __str__(self) -> str:
        return f"{self.student} L{self.level.number} {self.mode} {self.status}"

    @property
    def is_exam(self) -> bool:
        return self.mode == self.EXAM

    @property
    def total_questions(self) -> int:
        return len(self.question_ids)

    @property
    def answered_count(self) -> int:
        return self.responses.count()

    def current_question_id(self) -> int | None:
        """The first question not answered yet (None when all are answered)."""
        done = set(self.responses.values_list("question_id", flat=True))
        return next((qid for qid in self.question_ids if qid not in done), None)


class Response(models.Model):
    """One answer to one question in a session."""

    session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name="responses")
    question = models.ForeignKey("learning.Question", on_delete=models.CASCADE)
    answer = models.JSONField(default=list)
    is_correct = models.BooleanField(default=False)
    marks = models.PositiveSmallIntegerField(default=0)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["pk"]
        constraints = [models.UniqueConstraint(fields=["session", "question"], name="one_answer_per_question")]


class Badge(models.Model):
    """A badge earned by a student (each badge only once)."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badges")
    name = models.CharField(max_length=60)
    icon = models.CharField(max_length=40, default="award")
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["earned_at"]
        constraints = [models.UniqueConstraint(fields=["student", "name"], name="one_badge_name_per_student")]

    def __str__(self) -> str:
        return f"{self.student}: {self.name}"
