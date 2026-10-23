"""test_quizzes.py - Practice, exam, scoring, level up and Level Packs. Owners: Jihe Qi / Anish Shrestha."""
import random

import pytest

from apps.core.exceptions import AccessDeniedError, LevelLockedError, ValidationError
from apps.licensing.services import LevelPackService
from apps.quizzes.models import Assignment, Badge, ExamRules, QuizSession
from apps.quizzes.progression import LevelProgressionService
from apps.quizzes.scoring import ScoringService
from apps.quizzes.services import QuizService
from apps.schools.models import School

pytestmark = pytest.mark.django_db


def _answer_all(service, session, correct_count):
    for i in range(session.total_questions):
        q = service.current_question(session)
        wrong = [o.label for o in q.options if not o.is_correct]
        service.submit_answer(session, q.correct_labels if i < correct_count else [wrong[0]])
    session.refresh_from_db()
    return session


def test_exam_rules_pick_five_per_category():
    pool = {c: list(range(i * 10, i * 10 + 8)) for i, c in enumerate(["A", "B", "C", "D"])}
    ids = ExamRules(1).build(pool, ["A", "B", "C", "D"], random.Random(1))
    assert len(ids) == 20 and len(set(ids)) == 20
    for i in range(4):
        assert sum(1 for x in ids if i * 10 <= x < i * 10 + 10) == 5


def test_exam_rules_fill_gaps_and_fail_when_too_few():
    ids = ExamRules(1).build({"A": list(range(3)), "B": list(range(10, 27))}, ["A", "B", "C", "D"])
    assert len(ids) == 20
    with pytest.raises(ValidationError):
        ExamRules(1).build({"A": [1, 2]}, ["A"])


@pytest.mark.parametrize("pct, label", [(95, "Excellent"), (75, "Good"), (50, "Developing"), (10, "Needs more practice")])
def test_awareness_levels_never_say_fail(pct, label):
    assert ScoringService.awareness_level(pct) == label


def test_practice_gives_instant_feedback(user):
    service = QuizService(random.Random(3))
    session = service.start_practice(user("tama.ngata"), 1)
    q = service.current_question(session)
    fb = service.submit_answer(session, q.correct_labels)
    assert fb["is_correct"] and fb["headline"]


def test_full_exam_100_percent_gives_badges_and_certificate(user):
    ella = user("ella.johnson")
    Assignment.objects.get_or_create(level_id=4, section=ella.student_profile.section)
    school = ella.school
    LevelPackService.add_pack(school, 4)
    service = QuizService(random.Random(5))
    session = _answer_all(service, service.start_exam(ella, 4), 20)
    assert session.percentage == 100 and session.passed and session.awareness_level == "Excellent"
    assert Badge.objects.filter(student=ella, name__in=["Cyber Guardian", "Perfect Score"]).count() == 2


def test_exam_needs_assignment(user):
    ravi = user("ravi.singh")
    Assignment.objects.filter(section=ravi.student_profile.section, level__number=2).delete()
    with pytest.raises(AccessDeniedError):
        QuizService().start_exam(ravi, 2)


def test_level_locked_without_pass(user):
    with pytest.raises(LevelLockedError):
        QuizService().start_practice(user("wiremu.tipoki"), 2)


def test_tc24_passed_without_pack_says_ask_your_teacher(user, login):
    bikash = user("bikash.thapa")
    statuses = {s.level.number: s for s in LevelProgressionService().statuses(bikash)}
    assert statuses[2].status == "passed" and statuses[3].status == "need_pack"
    body = login("bikash.thapa").get("/quiz/").content.decode()
    assert "Ask your teacher" in body and "$" not in body          # students never see prices


def test_tc25_score_69_does_not_unlock(user, settings):
    tama = user("tama.ngata")
    section = tama.student_profile.section
    Assignment.objects.get_or_create(level_id=3, section=section)
    service = QuizService(random.Random(9))
    session = _answer_all(service, service.start_exam(tama, 3), 13)       # 65%
    assert not session.passed and session.awareness_level == "Developing"
    assert not LevelProgressionService().can_access(tama, 4)


def test_teacher_question_only_in_practice_of_own_school():
    from apps.learning.models import Question
    teacher_q = Question.objects.filter(created_by__isnull=False).first()
    bright, ktm = School.objects.get(code="BRIGHTSTAR"), School.objects.get(code="KTMVALLEY")
    assert Question.objects.for_practice(1, bright).filter(pk=teacher_q.pk).exists()
    assert not Question.objects.for_practice(1, ktm).filter(pk=teacher_q.pk).exists()
    assert not Question.objects.system().filter(pk=teacher_q.pk).exists()


def test_student_cannot_open_another_students_quiz(login):
    other = QuizSession.objects.filter(student__username="ella.johnson").first()
    assert login("tama.ngata").get(f"/quiz/session/{other.pk}/result/").status_code == 403


def test_answering_twice_is_blocked(user):
    service = QuizService()
    session = service.start_practice(user("aria.smith"), 1)
    q = service.current_question(session)
    service.submit_answer(session, q.correct_labels)
    from apps.quizzes.models import Response
    with pytest.raises(Exception):
        Response.objects.create(session=session, question_id=q.pk, answer=["A"])


def test_teacher_assigns_exam_and_students_are_notified(login):
    from apps.notifications.models import Notification
    c = login("sione.faleolo")
    section = School.objects.get(code="BRIGHTSTAR").classes.get(name="Year 7").sections.get(name="7B")
    c.post("/quiz/teacher/assignments/", {"section": section.pk, "level": 2, "due_date": "2026-11-01"})
    assert Assignment.objects.filter(section=section, level__number=2).exists()
    assert Notification.objects.filter(recipient__username="hana.kingi", message__contains="Level 2").exists()


def test_guest_quiz_scores_without_saving(client):
    before = QuizSession.objects.count()
    r = client.get("/quiz/guest/try/")
    assert r.status_code == 200
    assert QuizSession.objects.count() == before
