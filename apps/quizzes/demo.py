"""
demo.py - Demo assignments, exams and practice for seed_demo
============================================================

Owner: Anish Shrestha. Exams run through the real QuizService so scores,
badges, levels, certificates and notifications are all real.
"""
from __future__ import annotations

from datetime import timedelta

from apps.core.clock import today
from apps.learning.models import Level

from .models import Assignment
from .services import QuizService


def _assign(section, level_number, teacher, days=21):
    Assignment.objects.get_or_create(level=Level.objects.get(number=level_number), section=section,
                                     defaults={"teacher": teacher, "due_date": today() + timedelta(days=days)})


def _sit_exam(quiz, student, level, percentage, rng):
    session = quiz.start_exam(student, level)
    total = session.total_questions
    right = set(rng.sample(range(total), round(total * percentage / 100)))
    for position in range(total):
        q = quiz.current_question(session)
        wrong = [o.label for o in q.options if not o.is_correct]
        quiz.submit_answer(session, q.correct_labels if position in right or not wrong else [wrong[0]])


def _practice(quiz, student, level, rng):
    session = quiz.start_practice(student, level)
    for _ in range(session.total_questions):
        q = quiz.current_question(session)
        wrong = [o.label for o in q.options if not o.is_correct]
        quiz.submit_answer(session, q.correct_labels if rng.random() < 0.7 or not wrong else [wrong[0]])


def load_demo_activity(p: dict, rng) -> int:
    """Assignments for Bright Star and Kathmandu Valley, then real exam attempts."""
    for section in list(p["y7"].values()) + list(p["y8"].values()):
        _assign(section, 1, p["sione"])
    for section in (p["y7"]["7A"], p["y8"]["8A"]):
        _assign(section, 2, p["sione"])
    _assign(p["y8"]["8A"], 3, p["sione"])
    for section in p["c7"].values():
        _assign(section, 1, p["sita"])
    _assign(p["c7"]["Everest"], 2, p["sita"])
    quiz = QuizService(rng=rng)
    s7a, s8a, ev = p["s7a"], p["s8a"], p["everest"]
    plan = [(s7a["Tama"], [(1, 85), (2, 75)]), (s7a["Aria"], [(1, 95)]), (s7a["Wiremu"], [(1, 45)]),
            (s7a["Losa"], [(1, 70)]), (s7a["Aashish"], [(1, 60)]), (s7a["Jack"], [(1, 80)]),
            (s7a["Manaia"], [(1, 90), (2, 60)]), (s8a["Ella"], [(1, 100), (2, 85), (3, 75)]), (s8a["Ravi"], [(1, 72)]),
            (s8a["Moana"], [(1, 55)]), (ev["Bikash"], [(1, 90), (2, 80)]), (ev["Pooja"], [(1, 75)]),
            (ev["Suman"], [(1, 40)]), (ev["Anjali"], [(1, 85)])]
    exams = 0
    for student, attempts in plan:
        for level, pct in attempts:
            _sit_exam(quiz, student, level, pct, rng)
            exams += 1
    for student in (s7a["Tama"], s7a["Wiremu"], ev["Bikash"], ev["Rojan"]):
        _practice(quiz, student, 1, rng)
    return exams
