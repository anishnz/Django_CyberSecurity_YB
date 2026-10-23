"""
views.py - BI dashboards, school reports, class and student reports, CSV/PDF export
===================================================================================

Owners: Dinesh Upreti (screens and charts, task D-15), Rajneesh Kumar (queries)
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from apps.accounts.decorators import role_required, super_admin_required
from apps.core import clock
from apps.core.exceptions import AccessDeniedError
from apps.schools.models import School, Section

from .services import CLASS_COLUMNS, SCHOOL_COLUMNS, BIService

User = get_user_model()


def _download(content, filename: str, content_type: str) -> HttpResponse:
    response = HttpResponse(content, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@super_admin_required
def bi_dashboard(request):
    """Business intelligence for the whole platform (Super Admin)."""
    bi = BIService()
    rows = bi.school_table()
    if request.GET.get("export") == "csv":
        return _download(bi.to_csv(rows, SCHOOL_COLUMNS), "cyberquest_schools.csv", "text/csv")
    mix = bi.plan_mix()
    return render(request, "reports/bi_dashboard.html", {
        "kpis": bi.platform_kpis(), "rows": rows, "tickets": bi.ticket_stats(), "categories": bi.category_strength(),
        "levels": bi.level_pass_rates(), "expiring": bi.licences_ending(30), "pending_payments": bi.pending_payments(),
        "charts": {"activity": bi.monthly_activity(), "plans": {"labels": list(mix), "values": list(mix.values())}}})


def _school_for(request) -> School:
    if request.user.is_super_admin:
        return get_object_or_404(School, pk=request.GET.get("school") or 0)
    return request.user.school


@role_required("super_admin", "school_admin")
def school_bi(request):
    """One school's numbers. Super Admin adds ?school=<id> (or uses Login as)."""
    if request.user.is_super_admin and not request.GET.get("school"):
        return render(request, "reports/school_pick.html", {"schools": School.objects.order_by("name")})
    school = _school_for(request)
    bi = BIService()
    return render(request, "reports/school_bi.html", {
        "school": school, "kpis": bi.school_kpis(school), "sections": bi.section_summary(school),
        "categories": bi.category_strength(school), "levels": bi.level_pass_rates(school),
        "charts": {"activity": bi.monthly_activity(school)}})


def _sections_for(user):
    qs = Section.objects.select_related("school_class", "school_class__school").order_by("school_class__year_level", "name")
    return qs if user.is_super_admin else qs.filter(school_class__school=user.school)


@role_required("super_admin", "school_admin", "teacher")
def class_report_pick(request):
    return render(request, "reports/class_pick.html", {"sections": _sections_for(request.user)})


@role_required("super_admin", "school_admin", "teacher")
def class_report(request, pk):
    section = get_object_or_404(_sections_for(request.user), pk=pk)
    bi = BIService()
    rows = bi.class_report(section)
    title = f"Class report – {section.label}"
    subtitle = f"{section.school.name} · made {clock.today():%d %b %Y} · first names only"
    fmt = request.GET.get("export")
    if fmt == "csv":
        return _download(bi.to_csv(rows, CLASS_COLUMNS), f"class_report_{section.pk}.csv", "text/csv")
    if fmt == "pdf":
        return _download(bi.to_pdf(title, subtitle, rows, CLASS_COLUMNS), f"class_report_{section.pk}.pdf", "application/pdf")
    students = User.objects.filter(student_profile__section=section)
    return render(request, "reports/class_report.html", {"section": section, "rows": rows, "title": title,
                                                         "categories": bi.category_strength(students=students)})


@role_required("super_admin", "school_admin", "teacher")
def student_report(request, pk):
    student = get_object_or_404(User.objects.select_related("school", "student_profile"), pk=pk, role="student")
    if not request.user.is_super_admin and student.school_id != request.user.school_id:
        raise AccessDeniedError("This student is not in your school.")
    return render(request, "reports/student_report.html", BIService().student_report(student))
