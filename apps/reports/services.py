"""
services.py - Business intelligence and reports (one place for every number)
============================================================================

Owner: Dinesh Upreti (task D-15) with Rajneesh Kumar (queries, task R-16)

* Platform BI (Super Admin): schools, students, exams, monthly income from
  licences, plan mix, activity per month, tickets, payments.
* School BI (School Admin): the same numbers for one school.
* Class report (Teacher): one row per student in a section, CSV and PDF export.
* Student report: levels, best scores and categories to practise.

Privacy (NFR): reports show first names and usernames only, never parent details.
All numbers come from the database with aggregate queries (no loops over every row).
"""
from __future__ import annotations

import csv
import io
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, F, Max, Q
from django.db.models.functions import TruncMonth

from apps.core import clock
from apps.learning.categories import CATEGORIES
from apps.licensing.models import License
from apps.quizzes.models import QuizSession, Response
from apps.schools.models import School, StudentProfile

User = get_user_model()


def _exams(school=None):
    qs = QuizSession.objects.filter(mode="exam", status="finished")
    return qs.filter(student__school=school) if school else qs


def _round(value, places=1):
    return round(value or 0, places)


class BIService:
    """Business intelligence numbers for dashboards, charts and exports."""

    # ----------------------------------------------------------- platform
    def platform_kpis(self) -> dict:
        exams = _exams().aggregate(n=Count("pk"), avg=Avg("percentage"), passed=Count("pk", filter=Q(passed=True)))
        return {
            "schools": School.objects.filter(is_active=True).count(),
            "students": User.objects.filter(role="student", is_active=True).count(),
            "teachers": User.objects.filter(role="teacher", is_active=True).count(),
            "exams finished": exams["n"],
            "average score %": _round(exams["avg"]),
            "pass rate %": _round(100 * exams["passed"] / exams["n"]) if exams["n"] else 0,
            "monthly income (NZD)": f"{self.monthly_income():,.2f}",
        }

    @staticmethod
    def monthly_income() -> Decimal:
        """Licence income per month from active paid plans (after community discount)."""
        today = clock.today()
        total = Decimal("0")
        for lic in License.objects.select_related("school").filter(school__is_active=True):
            plan = lic.plan_obj
            if plan.is_active(today):
                total += plan.monthly_price()
        return total

    @staticmethod
    def licences_ending(days: int = 30):
        today = clock.today()
        return (License.objects.select_related("school")
                .filter(expiry_date__gte=today, expiry_date__lte=today + timedelta(days=days)).order_by("expiry_date"))

    @staticmethod
    def pending_payments() -> int:
        try:
            from apps.payments.models import Payment  # pylint: disable=import-outside-toplevel
        except ImportError:
            return 0
        return Payment.objects.filter(status="pending").count()

    @staticmethod
    def open_tickets(school=None) -> int:
        from apps.helpdesk.models import Ticket  # pylint: disable=import-outside-toplevel
        qs = Ticket.objects.exclude(status__in=[Ticket.RESOLVED, Ticket.CLOSED])
        return qs.filter(school=school).count() if school else qs.count()

    @staticmethod
    def plan_mix() -> dict:
        rows = License.objects.values("plan").annotate(n=Count("pk")).order_by("plan")
        return {r["plan"]: r["n"] for r in rows}

    @staticmethod
    def monthly_activity(school=None, months: int = 6) -> dict:
        """Exams per month and the average score (for a line/bar chart)."""
        start = clock.today().replace(day=1) - timedelta(days=31 * (months - 1))
        rows = (_exams(school).filter(finished_at__date__gte=start.replace(day=1)).annotate(m=TruncMonth("finished_at"))
                .values("m").annotate(n=Count("pk"), avg=Avg("percentage")).order_by("m"))
        return {"labels": [r["m"].strftime("%b %Y") for r in rows], "exams": [r["n"] for r in rows],
                "average": [_round(r["avg"]) for r in rows]}

    @staticmethod
    def category_strength(school=None, students=None) -> list[dict]:
        """Percentage of correct answers per category, weakest first (what to teach next)."""
        qs = Response.objects.filter(session__mode="exam", session__status="finished")
        if school:
            qs = qs.filter(session__student__school=school)
        if students is not None:
            qs = qs.filter(session__student__in=students)
        rows = qs.values(cat=F("question__category")).annotate(n=Count("pk"), ok=Count("pk", filter=Q(is_correct=True)))
        out = [{"code": r["cat"], "name": CATEGORIES.get(r["cat"], (r["cat"], ""))[0], "answers": r["n"],
                "percent": _round(100 * r["ok"] / r["n"]) if r["n"] else 0} for r in rows]
        return sorted(out, key=lambda r: r["percent"])

    @staticmethod
    def level_pass_rates(school=None) -> list[dict]:
        rows = (_exams(school).values(number=F("level__number"))
                .annotate(n=Count("pk"), passed=Count("pk", filter=Q(passed=True)), avg=Avg("percentage")).order_by("number"))
        return [{"level": r["number"], "exams": r["n"], "pass_rate": _round(100 * r["passed"] / r["n"]) if r["n"] else 0,
                 "average": _round(r["avg"])} for r in rows]

    def school_table(self) -> list[dict]:
        """One row per school: business performance at a glance."""
        today = clock.today()
        exam_stats = {r["student__school"]: r for r in _exams().values("student__school").annotate(
            n=Count("pk"), avg=Avg("percentage"), passed=Count("pk", filter=Q(passed=True)), last=Max("finished_at"))}
        students = dict(User.objects.filter(role="student", is_active=True).values("school").annotate(n=Count("pk"))
                        .values_list("school", "n"))
        out = []
        for school in School.objects.select_related("license").order_by("name"):
            lic = getattr(school, "license", None)
            plan = lic.plan_obj if lic else None
            ex = exam_stats.get(school.pk, {})
            out.append({
                "school": school, "students": students.get(school.pk, 0), "exams": ex.get("n", 0),
                "average": _round(ex.get("avg")), "pass_rate": _round(100 * ex["passed"] / ex["n"]) if ex.get("n") else 0,
                "last_exam": ex.get("last"), "plan": lic.get_plan_display() if lic else "None",
                "status": plan.status_label(today) if plan else "No licence",
                "income": plan.monthly_price() if plan and plan.is_active(today) else Decimal("0"),
                "open_tickets": self.open_tickets(school)})
        return out

    @staticmethod
    def ticket_stats(school=None) -> dict:
        from apps.helpdesk.models import Ticket  # pylint: disable=import-outside-toplevel
        from apps.helpdesk.services import TicketService  # pylint: disable=import-outside-toplevel
        qs = Ticket.objects.filter(school=school) if school else Ticket.objects.all()
        by_status = dict(qs.values_list("status").annotate(n=Count("pk")).values_list("status", "n"))
        done = [t.resolved_at - t.created_at for t in qs.filter(resolved_at__isnull=False).only("resolved_at", "created_at")[:500]]
        hours = _round(sum(d.total_seconds() for d in done) / 3600 / len(done)) if done else 0
        overdue = sum(1 for t in qs.exclude(status__in=[Ticket.RESOLVED, Ticket.CLOSED]) if TicketService.is_overdue(t))
        return {"by_status": {label: by_status.get(code, 0) for code, label in Ticket.STATUSES},
                "average_hours_to_resolve": hours, "overdue": overdue}

    # ------------------------------------------------------------- school
    def school_kpis(self, school) -> dict:
        exams = _exams(school).aggregate(n=Count("pk"), avg=Avg("percentage"), passed=Count("pk", filter=Q(passed=True)))
        profiles = StudentProfile.objects.filter(user__school=school, user__is_active=True)
        return {
            "students": profiles.count(),
            "teachers": User.objects.filter(role="teacher", school=school, is_active=True).count(),
            "exams finished": exams["n"],
            "average score %": _round(exams["avg"]),
            "pass rate %": _round(100 * exams["passed"] / exams["n"]) if exams["n"] else 0,
            "family consent missing": profiles.filter(family_consent=False).count(),
            "open tickets": self.open_tickets(school),
        }

    @staticmethod
    def section_summary(school) -> list[dict]:
        rows = []
        for sec in school.classes.prefetch_related("sections").all():
            for s in sec.sections.all():
                st = _exams().filter(student__student_profile__section=s).aggregate(
                    n=Count("pk"), avg=Avg("percentage"), passed=Count("pk", filter=Q(passed=True)))
                rows.append({"section": s, "students": s.student_count, "exams": st["n"], "average": _round(st["avg"]),
                             "pass_rate": _round(100 * st["passed"] / st["n"]) if st["n"] else 0})
        return rows

    # -------------------------------------------------------------- class
    @staticmethod
    def class_report(section) -> list[dict]:
        """One row per student in a section (first name and username only)."""
        profiles = section.students.select_related("user").filter(user__is_active=True)
        stats = {r["student"]: r for r in _exams().filter(student__student_profile__section=section).values("student")
                 .annotate(n=Count("pk"), best=Max("percentage"), avg=Avg("percentage"), last=Max("finished_at"),
                           passed=Count("level", filter=Q(passed=True), distinct=True))}
        rows = []
        for p in profiles:
            s = stats.get(p.user_id, {})
            rows.append({"name": p.user.first_name or p.user.username, "username": p.user.username,
                         "level": p.current_level, "exams": s.get("n", 0), "levels_passed": s.get("passed", 0),
                         "best": _round(s.get("best")), "average": _round(s.get("avg")), "last": s.get("last"),
                         "consent": p.family_consent, "user_id": p.user_id})
        return rows

    @staticmethod
    def student_report(student) -> dict:
        sessions = _exams().filter(student=student).select_related("level").order_by("-finished_at")
        best = sessions.values(number=F("level__number")).annotate(best=Max("percentage"), tries=Count("pk")).order_by("number")
        return {"student": student, "sessions": sessions[:20], "best": list(best),
                "practice": QuizSession.objects.filter(student=student, mode="practice").count(),
                "weak": BIService.category_strength(students=[student])[:3]}

    # ------------------------------------------------------------ exports
    @staticmethod
    def to_csv(rows: list[dict], columns: list[tuple[str, str]]) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([label for _, label in columns])
        for r in rows:
            writer.writerow([_cell(r.get(key)) for key, _ in columns])
        return buf.getvalue()

    @staticmethod
    def to_pdf(title: str, subtitle: str, rows: list[dict], columns: list[tuple[str, str]]) -> bytes:
        """A simple A4 landscape table (reportlab)."""
        # pylint: disable=import-outside-toplevel
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from apps.core.pdf import register_fonts, styles as pdf_styles
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4), title=title, leftMargin=30, rightMargin=30)
        styles = pdf_styles()
        regular, bold = register_fonts()
        data = [[label for _, label in columns]] + [[_cell(r.get(k)) for k, _ in columns] for r in rows]
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b3d5c")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, -1), regular), ("FONTNAME", (0, 0), (-1, 0), bold), ("FONTSIZE", (0, 0), (-1, -1), 9), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d3dd")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f6f9")])]))
        doc.build([Paragraph(title, styles["Title"]), Paragraph(subtitle, styles["Normal"]), Spacer(1, 12), table])
        return buf.getvalue()


def _cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if hasattr(value, "strftime"):
        return value.strftime("%d %b %Y")
    return str(value)


CLASS_COLUMNS = [("name", "First name"), ("username", "Username"), ("level", "Current level"), ("exams", "Exams"),
                 ("levels_passed", "Levels passed"), ("best", "Best %"), ("average", "Average %"), ("last", "Last exam"),
                 ("consent", "Family consent")]
SCHOOL_COLUMNS = [("school", "School"), ("students", "Students"), ("exams", "Exams"), ("average", "Average %"),
                  ("pass_rate", "Pass rate %"), ("plan", "Plan"), ("status", "Licence"), ("income", "Monthly NZD"),
                  ("open_tickets", "Open tickets")]
