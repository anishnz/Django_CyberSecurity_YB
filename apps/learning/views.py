"""
views.py - Content pages (Super Admin) and "My questions" (teachers)
====================================================================

Owner: Anish Shrestha (task A-12)
"""

from __future__ import annotations

import json

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.decorators import role_required, super_admin_required

from .categories import LEVEL_CATEGORIES, category_name
from .forms import QuestionForm
from .importer import ContentImporter
from .models import Level, Question
from .services import QuestionService

staff = role_required("super_admin", "teacher")


@super_admin_required
def level_list(request):
    """All levels with their topics and number of questions."""
    levels = Level.objects.all()
    rows = [
        {
            "level": lvl,
            "topics": lvl.topics.count(),
            "questions": lvl.questions.filter(is_archived=False).count(),
            "teacher": lvl.questions.filter(created_by__isnull=False, is_archived=False).count(),
        }
        for lvl in levels
    ]
    return render(request, "learning/level_list.html", {"rows": rows})


@super_admin_required
def level_detail(request, number):
    """One level: topics and questions (staff view)."""
    level = get_object_or_404(Level, number=number)
    questions = (
        level.questions.filter(is_archived=False).prefetch_related("options").select_related("created_by", "school")
    )
    return render(
        request, "learning/level_detail.html", {"level": level, "questions": questions, "topics": level.topics.all()}
    )


@super_admin_required
@require_POST
def import_content(request):
    """Super Admin: reload the content files."""
    result = ContentImporter().import_all()
    messages.success(
        request,
        f"Content checked: {result['levels']} levels, {result['topics']} topics, "
        f"{result['questions_added']} new questions imported.",
    )
    return redirect("learning:level_list")


@role_required("teacher")
def my_questions(request):
    rows = Question.objects.filter(created_by=request.user, is_archived=False).select_related("level")
    return render(request, "learning/my_questions.html", {"rows": rows})


def _categories_json() -> str:
    return json.dumps({n: [[c, category_name(c, n)] for c in cats] for n, cats in LEVEL_CATEGORIES.items()})


@staff
def question_edit(request, pk=None):
    """Create or edit a question (teachers: own questions only; practice only)."""
    instance = get_object_or_404(Question, pk=pk) if pk else None
    initial = {}
    if instance:
        opts = {o.label: o for o in instance.options.all()}
        initial = {
            "level": instance.level.number,
            "category": instance.category,
            "q_type": instance.q_type,
            "scenario_text": instance.scenario_text,
            "text": instance.text,
            "feedback": instance.feedback,
            "correct": [lbl for lbl, o in opts.items() if o.is_correct],
            **{f"option_{k.lower()}": o.text for k, o in opts.items()},
        }
    form = QuestionForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        row = QuestionService().save(form.as_factory_data(), form.cleaned_data["q_type"], request.user, instance)
        messages.success(request, "Question saved. Ka pai!")
        if request.user.is_teacher:
            return redirect("learning:my_questions")
        return redirect("learning:level_detail", number=row.level.number)
    return render(
        request, "learning/question_form.html", {"form": form, "obj": instance, "categories": _categories_json()}
    )


@staff
@require_POST
def question_archive(request, pk):
    """Remove (archive) a practice question."""
    q = get_object_or_404(Question, pk=pk)
    QuestionService.archive(q, request.user)
    messages.success(request, "Question removed.")
    return redirect(request.META.get("HTTP_REFERER") or "learning:my_questions")
