"""
services.py - The quiz engine: start, answer, finish, review
=============================================================

Owner: Anish Shrestha (tasks A-14, A-15)

Flow:
    start_practice / start_exam -> QuizSession with ordered question ids
    submit_answer               -> Response row; PracticeMode gives feedback now
    finish (after last answer)  -> score, percentage, awareness level, passed,
                                   badges and level up (exam only), notifications
"""
from __future__ import annotations

import random
from collections import defaultdict

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.exceptions import AccessDeniedError, LevelLockedError, NotFoundError, ValidationError
from apps.core.models import SystemSettings
from apps.core.services import AuditService
from apps.learning.categories import category_name
from apps.learning.models import LearningTopic, Level, Question

from .feedback import FeedbackService
from .models import Assignment, ExamRules, QuizSession, Response
from .modes import mode_for
from .progression import LevelProgressionService
from .scoring import ScoringService


class QuizService:
    """Runs practice quizzes and level exams for students."""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        self.progression = LevelProgressionService()

    # ------------------------------------------------------------ checks
    def _check_student(self, student, level_number: int) -> Level:
        if not student.is_student:
            raise AccessDeniedError("Only students can take quizzes.")
        profile = getattr(student, "student_profile", None)
        if profile is None or not profile.can_play:
            raise AccessDeniedError("Your family (whānau) consent form is still waiting. Please ask your teacher.")
        level = Level.objects.filter(number=level_number).first()
        if level is None:
            raise NotFoundError("That level does not exist.")
        if not self.progression.can_access(student, level_number):
            raise LevelLockedError()
        return level

    @staticmethod
    def is_assigned(student, level_number: int) -> bool:
        section_id = getattr(getattr(student, "student_profile", None), "section_id", None)
        return Assignment.objects.filter(section_id=section_id, level__number=level_number).exists()

    @staticmethod
    def unfinished(student, level_number: int, mode: str) -> QuizSession | None:
        return QuizSession.objects.filter(student=student, level__number=level_number, mode=mode,
                                          status=QuizSession.IN_PROGRESS).first()

    # ------------------------------------------------------------- start
    def start_practice(self, student, level_number: int, category: str | None = None) -> QuizSession:
        level = self._check_student(student, level_number)
        if category and category not in level.categories:
            raise ValidationError("That category is not part of this level.")
        ids = list(Question.objects.for_practice(level_number, student.school, category).values_list("pk", flat=True))
        if not ids:
            raise ValidationError("There are no practice questions here yet.")
        self.rng.shuffle(ids)
        count = SystemSettings.load().practice_question_count
        ids = ids[:count]
        return QuizSession.objects.create(student=student, level=level, mode=QuizSession.PRACTICE,
                                          category=category or "", question_ids=ids, max_score=len(ids) * 5)

    def start_exam(self, student, level_number: int) -> QuizSession:
        level = self._check_student(student, level_number)
        if not self.is_assigned(student, level_number):
            raise AccessDeniedError("Your teacher has not assigned this exam yet.")
        existing = self.unfinished(student, level_number, QuizSession.EXAM)
        if existing:
            return existing
        pool = defaultdict(list)
        for pk, cat in Question.objects.system().filter(level=level).values_list("pk", "category"):
            pool[cat].append(pk)
        rules = ExamRules(level_number)
        ids = rules.build(pool, level.categories, self.rng)
        session = QuizSession.objects.create(student=student, level=level, mode=QuizSession.EXAM, question_ids=ids,
                                             max_score=rules.total_marks)
        AuditService.log(student, "exam_started", f"level {level_number}")
        return session

    # ------------------------------------------------------------ answer
    @staticmethod
    def get_session(student, session_id: int) -> QuizSession:
        session = QuizSession.objects.filter(pk=session_id).select_related("level").first()
        if session is None:
            raise NotFoundError("Quiz not found.")
        if session.student_id != student.pk:
            raise AccessDeniedError("This quiz belongs to another student.")
        return session

    @staticmethod
    def current_question(session: QuizSession):
        qid = session.current_question_id()
        if qid is None:
            return None
        return Question.objects.prefetch_related("options").select_related("level").get(pk=qid).as_domain()

    @transaction.atomic
    def submit_answer(self, session: QuizSession, answer) -> dict | None:
        """Save one answer; returns practice feedback (or None for exams)."""
        if session.status != QuizSession.IN_PROGRESS:
            raise ValidationError("This quiz is already finished.")
        question = self.current_question(session)
        if question is None:
            raise ValidationError("All questions are already answered.")
        labels = [a for a in (answer if isinstance(answer, (list, tuple)) else [answer]) if a]
        if not labels:
            raise ValidationError("Please choose an answer.")
        is_correct = question.check_answer(labels)
        try:
            Response.objects.create(session=session, question_id=question.pk, answer=sorted(labels),
                                    is_correct=is_correct, marks=question.marks_for(labels))
        except IntegrityError as exc:
            raise ValidationError("You have already answered this question.") from exc
        feedback = mode_for(session.mode).after_answer(question, is_correct)
        if feedback is not None:
            feedback["question"] = question
            feedback["your_answer"] = ", ".join(sorted(labels))
        if session.current_question_id() is None:
            self.finish(session)
        return feedback

    # ------------------------------------------------------------ finish
    def finish(self, session: QuizSession) -> QuizSession:
        responses = list(session.responses.all())
        session.score = sum(r.marks for r in responses)
        session.percentage = ScoringService.percentage(session.score, session.max_score)
        session.awareness_level = ScoringService.awareness_level(session.percentage)
        mode = mode_for(session.mode)
        session.passed = mode.counts_for_level() and ScoringService.has_passed(session.percentage,
                                                                                 self.progression.pass_mark())
        session.status = QuizSession.FINISHED
        session.finished_at = timezone.now()
        session.save()
        if mode.counts_for_level():
            AuditService.log(session.student, "exam_finished", f"level {session.level.number}",
                             new=f"{session.percentage}%")
            outcome = self.progression.after_exam(session.student, session.level.number, session.passed,
                                                  session.percentage)
            self._notify_exam(session)
            session.outcome = outcome  # attached for the result page
            if session.passed:
                self._issue_certificate(session)
        return session

    @staticmethod
    def _issue_certificate(session: QuizSession) -> None:
        """Make a PDF certificate for a passed level (certificates app, Dinesh)."""
        try:
            from apps.certificates.services import CertificateService  # pylint: disable=import-outside-toplevel
        except ImportError:
            return
        CertificateService().issue_for(session)

    @staticmethod
    def _notify_exam(session: QuizSession) -> None:
        from apps.notifications.services import notify  # pylint: disable=import-outside-toplevel
        from django.contrib.auth import get_user_model  # pylint: disable=import-outside-toplevel
        profile = getattr(session.student, "student_profile", None)
        teacher_ids = list(Assignment.objects.filter(section_id=getattr(profile, "section_id", None))
                           .exclude(teacher=None).values_list("teacher_id", flat=True))
        if not teacher_ids and session.student.school_id:
            teacher_ids = list(get_user_model().objects.filter(school_id=session.student.school_id, role="teacher")
                               .values_list("pk", flat=True))
        notify("exam_completed", {"student_id": session.student.pk, "student_name": session.student.get_full_name(),
                                  "level": session.level.number, "percentage": session.percentage,
                                  "passed": session.passed, "teacher_ids": teacher_ids, "session_id": session.pk})

    # ------------------------------------------------------------ review
    @staticmethod
    def review(session: QuizSession) -> list[dict]:
        """Every question with the student's answer, the safe answer and the explanation."""
        rows = []
        responses = {r.question_id: r for r in session.responses.all()}
        questions = {q.pk: q for q in Question.objects.filter(pk__in=session.question_ids).prefetch_related("options")
                     .select_related("level")}
        for qid in session.question_ids:
            q = questions[qid].as_domain()
            r = responses.get(qid)
            rows.append({"question": q, "answer": ", ".join(r.answer) if r else "–",
                         "is_correct": bool(r and r.is_correct), "marks": r.marks if r else 0})
        return rows

    @staticmethod
    def category_breakdown(session: QuizSession) -> list[dict]:
        totals = defaultdict(lambda: [0, 0])
        cats = dict(Question.objects.filter(pk__in=session.question_ids).values_list("pk", "category"))
        for r in session.responses.all():
            totals[cats[r.question_id]][0] += 1 if r.is_correct else 0
            totals[cats[r.question_id]][1] += 1
        return [{"code": c, "name": category_name(c, session.level.number), "correct": v[0], "total": v[1],
                 "pct": round(v[0] * 100 / v[1]) if v[1] else 0} for c, v in totals.items()]

    @staticmethod
    def topics_to_review(session: QuizSession):
        wrong_topics = set(Question.objects.filter(pk__in=session.responses.filter(is_correct=False)
                                                   .values_list("question_id", flat=True))
                           .values_list("topic_code", flat=True))
        return LearningTopic.objects.filter(code__in=wrong_topics)

    def result_context(self, session: QuizSession) -> dict:
        outcome = getattr(session, "outcome", None)
        if outcome is None and session.is_exam and session.passed:
            nxt = session.level.number + 1
            unlocked = nxt <= 6 and self.progression.can_access(session.student, nxt)
            outcome = {"badges": [], "next_level": nxt if nxt <= 6 else None,
                       "unlocked_level": nxt if unlocked else None, "next_level_needs_pack": nxt <= 6 and not unlocked}
        return {"session": session, "review": self.review(session), "breakdown": self.category_breakdown(session),
                "topics": self.topics_to_review(session), "outcome": outcome,
                "message": FeedbackService.result_message(session.percentage, session.passed, session.is_exam),
                "colour": ScoringService.awareness_colour(session.awareness_level),
                "pass_mark": self.progression.pass_mark(), "safety": FeedbackService.safety_reminder()}

    # ------------------------------------------------------------- guest
    def guest_questions(self, count: int = 5):
        ids = list(Question.objects.system().filter(level__number=1).values_list("pk", flat=True))
        self.rng.shuffle(ids)
        return [q.as_domain() for q in Question.objects.filter(pk__in=ids[:count]).prefetch_related("options")
                .select_related("level")]

    @staticmethod
    def grade_guest(post) -> dict:
        ids = [int(x) for x in post.getlist("question_id") if x.isdigit()][:5]
        rows, score = [], 0
        for q in Question.objects.filter(pk__in=ids).prefetch_related("options").select_related("level"):
            d = q.as_domain()
            answer = post.getlist(f"answer_{q.pk}")
            ok = d.check_answer(answer)
            score += 1 if ok else 0
            rows.append({"question": d, "answer": ", ".join(answer) or "–", "is_correct": ok})
        return {"rows": rows, "score": score, "total": len(rows)}
