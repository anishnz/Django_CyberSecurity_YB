"""
views.py - Student learning path, quizzes and exams; teacher dashboard and assignments; guest quiz
==================================================================================================

Owners: Anish Shrestha (quiz logic); screens by Dinesh Upreti
"""

from __future__ import annotations

from datetime import date

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.decorators import role_required
from apps.core.exceptions import AccessDeniedError, LevelLockedError, NotFoundError, ValidationError
from apps.core.services import AuditService
from apps.learning.models import LearningTopic, Level
from apps.notifications.models import Notification
from apps.notifications.services import notify
from apps.schools.models import Section, StudentProfile

from .feedback import FeedbackService
from .models import Assignment, Badge, QuizSession
from .progression import LevelProgressionService
from .services import QuizService

User = get_user_model()
student_only = role_required("student")
teacher_only = role_required("teacher")


# ------------------------------------------------------------------ student
@student_only
def student_dashboard(request):
    """Level trail, current level, assigned exams, recent results, badges, tip of the day."""
    student = request.user
    statuses = LevelProgressionService().statuses(student)
    section_id = getattr(student.student_profile, "section_id", None)
    return render(
        request,
        "quizzes/student_dashboard.html",
        {
            "statuses": statuses,
            "current": next((s for s in statuses if s.current), statuses[0] if statuses else None),
            "assignments": Assignment.objects.filter(section_id=section_id).select_related("level"),
            "recent": QuizSession.objects.filter(student=student, status="finished").select_related("level")[:5],
            "badges": Badge.objects.filter(student=student),
            "tip": FeedbackService().tip_of_the_day(),
            "safety": FeedbackService.safety_reminder(),
            "notices": Notification.objects.filter(recipient=student)[:5],
        },
    )


@student_only
def level_page(request, number):
    """One level: its topics and the practice / exam buttons."""
    level = get_object_or_404(Level, number=number)
    service = QuizService()
    if not service.progression.can_access(request.user, number):
        raise LevelLockedError()
    best = service.progression.best_by_level(request.user).get(number)
    return render(
        request,
        "quizzes/level.html",
        {
            "level": level,
            "topics": level.topics.all(),
            "assigned": service.is_assigned(request.user, number),
            "unfinished": service.unfinished(request.user, number, "exam"),
            "best": best,
        },
    )


@student_only
def topic_page(request, code):
    """A learning topic page with its media and YouTube videos."""
    topic = get_object_or_404(LearningTopic.objects.select_related("level"), code=code)
    if not LevelProgressionService().can_access(request.user, topic.level.number):
        raise LevelLockedError()
    from apps.medialib.services import MediaService  # pylint: disable=import-outside-toplevel

    media, videos = MediaService.for_topic(topic, request.user)
    return render(
        request,
        "quizzes/topic.html",
        {"topic": topic, "siblings": topic.level.topics.all(), "media": media, "videos": videos},
    )


@student_only
@require_POST
def practice_start(request):
    level = int(request.POST.get("level", 1))
    session = QuizService().start_practice(request.user, level, request.POST.get("category") or None)
    return redirect("quizzes:question", pk=session.pk)


@student_only
@require_POST
def exam_start(request):
    session = QuizService().start_exam(request.user, int(request.POST.get("level", 1)))
    return redirect("quizzes:question", pk=session.pk)


@student_only
def question(request, pk):
    """Show the current question of a session."""
    service = QuizService()
    session = service.get_session(request.user, pk)
    if session.status == "finished":
        return redirect("quizzes:result", pk=pk)
    q = service.current_question(session)
    number = session.answered_count + 1
    half = session.total_questions // 2
    return render(
        request,
        "quizzes/question.html",
        {
            "session": session,
            "question": q,
            "number": number,
            "progress": round((number - 1) * 100 / max(session.total_questions, 1)),
            "halfway": FeedbackService.halfway_message() if number == half + 1 and half > 1 else "",
        },
    )


@student_only
@require_POST
def answer(request, pk):
    """Save the student's answer; practice goes to feedback, exams go to the next question."""
    service = QuizService()
    session = service.get_session(request.user, pk)
    answer_feedback = service.submit_answer(session, request.POST.getlist("answer"))
    session.refresh_from_db()
    if answer_feedback is not None:
        q = answer_feedback.pop("question")
        request.session[f"fb_{pk}"] = {**answer_feedback, "text": q.text, "category": q.category_name}
        return redirect("quizzes:feedback", pk=pk)
    return redirect("quizzes:result" if session.status == "finished" else "quizzes:question", pk=pk)


@student_only
def feedback(request, pk):
    """Feedback after a practice answer (taken from the session, shown once)."""
    session = QuizService().get_session(request.user, pk)
    data = request.session.get(f"fb_{pk}")
    if not data:
        return redirect("quizzes:question", pk=pk)
    return render(
        request, "quizzes/feedback.html", {"session": session, "fb": data, "done": session.status == "finished"}
    )


@role_required("student", "teacher", "school_admin", "super_admin")
def result(request, pk):
    """The result page after a practice round or an exam."""
    session = get_object_or_404(QuizSession.objects.select_related("level", "student"), pk=pk)
    user = request.user
    if user.is_student and session.student_id != user.pk:
        raise AccessDeniedError("This result belongs to another student.")
    if not user.is_student and not user.is_super_admin and session.student.school_id != user.school_id:
        raise AccessDeniedError("You can only see results from your own school.")
    if session.status != "finished":
        return redirect("quizzes:question", pk=pk)
    return render(request, "quizzes/result.html", QuizService().result_context(session))


@student_only
def my_results(request):
    sessions = QuizSession.objects.filter(student=request.user, status="finished").select_related("level")
    best = LevelProgressionService.best_by_level(request.user)
    return render(
        request,
        "quizzes/my_results.html",
        {"sessions": sessions, "best": sorted(best.items()), "badges": Badge.objects.filter(student=request.user)},
    )


# ------------------------------------------------------------------ teacher
def _teacher_sections(user):
    return Section.objects.filter(school_class__school=user.school).select_related("school_class")


@teacher_only
def teacher_dashboard(request):
    """Teacher home: sections, recent exam results, assignments and notices."""
    school = request.user.school
    sections = _teacher_sections(request.user)
    recent = QuizSession.objects.filter(student__school=school, mode="exam", status="finished").select_related(
        "student", "level"
    )[:10]
    stats = QuizSession.objects.filter(student__school=school, mode="exam", status="finished").aggregate(
        n=Count("pk"), avg=Avg("percentage")
    )
    return render(
        request,
        "quizzes/teacher_dashboard.html",
        {
            "sections": sections,
            "recent": recent,
            "stats": stats,
            "assignments": Assignment.objects.filter(section__school_class__school=school).select_related(
                "level", "section"
            ),
            "notices": Notification.objects.filter(recipient=request.user)[:5],
            "no_consent": StudentProfile.objects.filter(user__school=school, family_consent=False).count(),
        },
    )


@teacher_only
def assignment_list(request):
    """List exam assignments and assign a level exam to a section."""
    school = request.user.school
    if request.method == "POST":
        section = get_object_or_404(Section, pk=request.POST.get("section"), school_class__school=school)
        level = get_object_or_404(Level, number=request.POST.get("level"))
        due_text = request.POST.get("due_date", "")
        try:
            due = date.fromisoformat(due_text) if due_text else None
        except ValueError as exc:
            raise ValidationError("Please choose a valid due date.") from exc
        _, created = Assignment.objects.update_or_create(
            level=level, section=section, defaults={"teacher": request.user, "due_date": due}
        )
        AuditService.log(request.user, "exam_assigned", f"level {level.number} -> {section}")
        notify(
            "exam_assigned",
            {
                "level": level.number,
                "due": due.strftime("%d %b") if due else "",
                "student_ids": list(section.students.values_list("user_id", flat=True)),
            },
        )
        from apps.licensing.services import LevelPackService  # pylint: disable=import-outside-toplevel

        if not LevelPackService().has_pack(school, level.number):
            messages.warning(
                request,
                f"Assigned. Your school does not own Level Pack {level.number} yet, so students "
                "will see it as locked until it is added.",
            )
        else:
            messages.success(request, f"Exam {'assigned' if created else 'updated'} for {section}. Ka pai!")
        return redirect("quizzes:assignment_list")
    return render(
        request,
        "quizzes/assignments.html",
        {
            "assignments": Assignment.objects.filter(section__school_class__school=school).select_related(
                "level", "section__school_class"
            ),
            "sections": _teacher_sections(request.user),
            "levels": Level.objects.all(),
        },
    )


@teacher_only
@require_POST
def assignment_delete(request, pk):
    """Remove an assignment (finished results are kept)."""
    obj = get_object_or_404(Assignment, pk=pk, section__school_class__school=request.user.school)
    AuditService.log(request.user, "exam_unassigned", str(obj))
    obj.delete()
    messages.success(request, "Assignment removed.")
    return redirect("quizzes:assignment_list")


# -------------------------------------------------------------------- guest
def guest_try(request):
    """Demo Guest (or a visitor) tries 5 Level 1 questions. Nothing is saved."""
    service = QuizService()
    if request.method == "POST":
        return render(request, "quizzes/guest_result.html", service.grade_guest(request.POST))
    questions = service.guest_questions()
    if not questions:
        raise NotFoundError("No questions are loaded yet.")
    return render(request, "quizzes/guest_try.html", {"questions": questions})
