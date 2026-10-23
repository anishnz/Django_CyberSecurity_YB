"""
models.py - Levels, study topics, questions and answer options
==============================================================

Owner: Anish Shrestha (task A-11)

The database rows hold the data. The rules for marking live in the Question
classes in questions.py; ``Question.as_domain()`` uses the QuestionFactory to
turn a row into the right class (SingleChoice, TrueFalse, MultiSelect, Scenario).
"""
from __future__ import annotations

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .categories import CATEGORY_CHOICES, LEVEL_CATEGORIES, category_icon, category_name

MARKS_PER_QUESTION = 5
Q_TYPES = [("single", "Single choice"), ("true_false", "True or false"),
           ("multi_select", "Choose all that apply"), ("scenario", "Scenario")]


class Level(models.Model):
    """One of the six learning levels (Cyber Starter … Cyber Pro)."""

    number = models.PositiveSmallIntegerField(unique=True, validators=[MinValueValidator(1), MaxValueValidator(6)])
    name = models.CharField(max_length=60)
    audience = models.CharField(max_length=60)
    is_free = models.BooleanField(default=False)
    icon = models.CharField(max_length=40, default="shield")
    description = models.TextField()

    class Meta:
        ordering = ["number"]

    def __str__(self) -> str:
        return self.title

    @property
    def title(self) -> str:
        return f"Level {self.number} – {self.name}"

    @property
    def categories(self) -> list[str]:
        return LEVEL_CATEGORIES.get(self.number, [])

    @property
    def category_pairs(self) -> list[tuple[str, str]]:
        return [(code, category_name(code, self.number)) for code in self.categories]


class LearningTopic(models.Model):
    """A short study topic (2–7 minutes of reading)."""

    code = models.CharField(max_length=10, unique=True)
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="topics")
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=120)
    summary = models.CharField(max_length=300, blank=True)
    body = models.TextField()
    habits = models.TextField(blank=True, help_text="One good habit per line.")
    kiwi_example = models.TextField(blank=True)
    minutes = models.PositiveSmallIntegerField(default=3)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["level__number", "sort_order", "code"]

    def __str__(self) -> str:
        return f"{self.code} {self.title}"

    @property
    def habit_list(self) -> list[str]:
        return [h.strip("- ").strip() for h in self.habits.splitlines() if h.strip()]

    @property
    def category_name(self) -> str:
        return category_name(self.category, self.level.number)

    @property
    def icon(self) -> str:
        return category_icon(self.category)


class QuestionQuerySet(models.QuerySet):
    """Ready-made queries (Repository idea)."""

    def approved(self):
        return self.filter(approved=True, is_archived=False)

    def system(self):
        """Questions written by CyberQuest (used in exams)."""
        return self.approved().filter(created_by__isnull=True)

    def for_practice(self, level_number: int, school=None, category: str | None = None):
        """System questions + the school's own teacher questions."""
        qs = self.approved().filter(level__number=level_number)
        qs = qs.filter(models.Q(created_by__isnull=True) | models.Q(school=school)) if school else qs.filter(created_by__isnull=True)
        return qs.filter(category=category) if category else qs


class Question(models.Model):
    """One question row. Teacher questions have ``created_by`` and ``school``."""

    code = models.CharField(max_length=30, unique=True, null=True, blank=True)
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="questions")
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    q_type = models.CharField(max_length=20, choices=Q_TYPES, default="single")
    topic_code = models.CharField(max_length=10, blank=True)
    text = models.CharField(max_length=400)
    scenario_text = models.TextField(blank=True)
    feedback = models.TextField()
    marks = models.PositiveSmallIntegerField(default=MARKS_PER_QUESTION)
    nz_context = models.BooleanField(default=False)
    approved = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="questions")
    school = models.ForeignKey("schools.School", null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = QuestionQuerySet.as_manager()

    class Meta:
        ordering = ["level__number", "category", "pk"]
        constraints = [models.CheckConstraint(condition=models.Q(marks=MARKS_PER_QUESTION), name="question_marks_5")]

    def __str__(self) -> str:
        return f"{self.code or self.pk}: {self.text[:60]}"

    @property
    def category_name(self) -> str:
        return category_name(self.category, self.level.number)

    @property
    def is_teacher_question(self) -> bool:
        return self.created_by_id is not None

    def as_domain(self):
        """The OOP Question object (factory picks the class from q_type)."""
        from .factory import QuestionFactory  # pylint: disable=import-outside-toplevel
        return QuestionFactory.from_model(self)


class AnswerOption(models.Model):
    """One answer choice A–D."""

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    label = models.CharField(max_length=1, choices=[(x, x) for x in "ABCD"])
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["label"]
        constraints = [models.UniqueConstraint(fields=["question", "label"], name="one_label_per_question")]

    def __str__(self) -> str:
        return f"{self.label}. {self.text}"
