"""
views.py - School management screens
====================================

Owner: Rajneesh Kumar (backend, tasks R-02 to R-04); screens by Dinesh Upreti
Super Admin: list/create schools, rename (overwrite warning), status, capacity.
School Admin: dashboard, classes and sections, students, teachers, CSV import.
"""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.decorators import role_required, super_admin_required
from apps.core.exceptions import AccessDeniedError, ValidationError
from apps.core.services import AuditService

from .forms import ClassForm, CsvImportForm, SchoolForm, SectionForm, StudentEditForm, StudentForm, TeacherForm
from .models import School, SchoolClass, Section, StudentProfile
from .services import PeopleService, SchoolService

User = get_user_model()
admin_only = role_required("school_admin")


def _my_school(request) -> School:
    school = request.user.school
    if school is None:
        raise AccessDeniedError("Your account is not linked to a school.")
    return school


# ----------------------------------------------------------- Super Admin
@super_admin_required
def school_list(request):
    schools = School.objects.select_related("license").annotate(
        users_n=Count("users", filter=Q(users__role="student"))).order_by("name")
    return render(request, "schools/school_list.html", {"schools": schools, "form": SchoolForm()})


@super_admin_required
def school_new(request):
    form = SchoolForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        school = SchoolService().create_school(data.pop("code"), data.pop("name"), request.user, **data)
        messages.success(request, f"{school.name} created with a 30-day Free Trial.")
        return redirect("schools:school_detail", pk=school.pk)
    return render(request, "schools/school_form.html", {"form": form})


@super_admin_required
def school_detail(request, pk):
    school = get_object_or_404(School, pk=pk)
    classes = school.classes.prefetch_related("sections")
    admins = User.objects.filter(school=school).exclude(role="student").order_by("role")
    from apps.integrations.services import map_for  # pylint: disable=import-outside-toplevel
    return render(request, "schools/school_detail.html", {"school": school, "classes": classes, "staff": admins,
                                                          "map": map_for(school.address, school.latitude, school.longitude)})


@super_admin_required
@require_POST
def school_rename(request, pk):
    """Overwrite warning: show old → new name first."""
    school = get_object_or_404(School, pk=pk)
    new_name = request.POST.get("name", "")
    if request.POST.get("confirmed") != "yes":
        if len(new_name.strip()) < 3:
            raise ValidationError("School name must have at least 3 characters.")
        return render(request, "core/confirm.html", {
            "title": "Rename school", "warning": "You are about to change the school name everywhere "
            "(dashboards, reports and certificates).", "changes": [("School name", school.name, new_name.strip())],
            "hidden": {"name": new_name, "confirmed": "yes"}, "cancel_url": "schools:school_detail", "cancel_arg": pk})
    old, new = SchoolService.rename(school, new_name, request.user)
    messages.success(request, f"School renamed from '{old}' to '{new}'.")
    return redirect("schools:school_detail", pk=pk)


@super_admin_required
@require_POST
def school_status(request, pk):
    school = get_object_or_404(School, pk=pk)
    SchoolService.set_active(school, not school.is_active, request.user)
    messages.success(request, f"{school.name} is now {'active' if school.is_active else 'switched off'}.")
    return redirect("schools:school_detail", pk=pk)


@super_admin_required
@require_POST
def section_capacity(request, pk):
    """Overwrite warning for capacity (Super Admin only)."""
    section = get_object_or_404(Section, pk=pk)
    service = SchoolService()
    value = request.POST.get("capacity", "")
    if request.POST.get("confirmed") != "yes":
        old, new = service.preview_capacity(section, value)
        return render(request, "core/confirm.html", {
            "title": "Change section capacity", "warning": f"Section {section.name} at {section.school.name}.",
            "changes": [("Capacity", old, new)], "hidden": {"capacity": value, "confirmed": "yes"},
            "cancel_url": "schools:school_detail", "cancel_arg": section.school.pk})
    old, new = service.change_capacity(section, value, request.user)
    messages.success(request, f"Section {section.name} capacity changed from {old} to {new}.")
    return redirect("schools:school_detail", pk=section.school.pk)


# ----------------------------------------------------------- School Admin
@admin_only
def admin_dashboard(request):
    school = _my_school(request)
    from apps.licensing.services import LevelPackService, LicenseService  # pylint: disable=import-outside-toplevel
    lic = LicenseService.get(school)
    from apps.core.clock import today  # pylint: disable=import-outside-toplevel
    sections = Section.objects.filter(school_class__school=school).select_related("school_class")
    return render(request, "schools/admin_dashboard.html", {
        "school": school, "licence": lic, "plan": lic.plan_obj if lic else None,
        "status": lic.plan_obj.status_label(today()) if lic else "",
        "packs": LevelPackService().table(school), "sections": sections,
        "teachers": User.objects.filter(school=school, role="teacher").count(),
        "students": StudentProfile.objects.filter(user__school=school).count(),
        "no_consent": StudentProfile.objects.filter(user__school=school, family_consent=False).count(),
    })


@admin_only
def class_list(request):
    school = _my_school(request)
    if request.method == "POST":
        kind = request.POST.get("kind")
        if kind == "class":
            form = ClassForm(request.POST)
            if form.is_valid():
                SchoolService.add_class(school, form.cleaned_data["name"], form.cleaned_data["year_level"], request.user)
                messages.success(request, "Class added.")
        elif kind == "section":
            form = SectionForm(request.POST)
            cls = get_object_or_404(SchoolClass, pk=request.POST.get("class_id"), school=school)
            if form.is_valid():
                section = SchoolService.add_section(cls, form.cleaned_data["name"], request.user)
                messages.success(request, f"Section {section.name} added (capacity {section.capacity}).")
        return redirect("schools:class_list")
    classes = school.classes.prefetch_related("sections__students")
    return render(request, "schools/class_list.html", {"school": school, "classes": classes,
                                                        "class_form": ClassForm(), "section_form": SectionForm()})


@admin_only
def student_list(request):
    school = _my_school(request)
    students = StudentProfile.objects.filter(user__school=school).select_related("user", "section__school_class")
    section_id, q = request.GET.get("section", ""), request.GET.get("q", "").strip()
    if section_id:
        students = students.filter(section_id=section_id)
    if q:
        students = students.filter(Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q)
                                   | Q(user__username__icontains=q))
    sections = Section.objects.filter(school_class__school=school).select_related("school_class")
    return render(request, "schools/student_list.html", {"school": school, "students": students, "sections": sections,
                                                          "section_id": section_id, "q": q})


@admin_only
def student_new(request):
    school = _my_school(request)
    form = StudentForm(request.POST or None, school=school)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        user = PeopleService().add_student(school, by=request.user, **data)
        messages.success(request, f"Student added. Username: {user.username}")
        return redirect("schools:student_list")
    return render(request, "schools/student_form.html", {"form": form, "school": school})


@admin_only
def student_edit(request, pk):
    school = _my_school(request)
    profile = get_object_or_404(StudentProfile, pk=pk, user__school=school)
    initial = {"section": profile.section, "family_consent": profile.family_consent, "parent_name": profile.parent_name,
               "parent_email": profile.parent_email, "parent_phone": profile.parent_phone,
               "parent_opt_in": profile.parent_opt_in}
    form = StudentEditForm(request.POST or None, school=school, initial=initial)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        PeopleService.move_student(profile, data["section"], request.user)
        profile.refresh_from_db()
        for key in ("family_consent", "parent_name", "parent_email", "parent_phone", "parent_opt_in"):
            setattr(profile, key, data[key])
        profile.save()
        AuditService.log(request.user, "student_updated", profile.user.username)
        messages.success(request, "Student saved.")
        return redirect("schools:student_list")
    return render(request, "schools/student_edit.html", {"form": form, "profile": profile})


@admin_only
@require_POST
def person_toggle(request, pk):
    school = _my_school(request)
    user = get_object_or_404(User, pk=pk, school=school, role__in=["student", "teacher"])
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    AuditService.log(request.user, "user_status", user.username, not user.is_active, user.is_active)
    messages.success(request, f"{user} is now {'on' if user.is_active else 'off'}.")
    return redirect(request.META.get("HTTP_REFERER") or "schools:student_list")


@admin_only
def teacher_list(request):
    school = _my_school(request)
    form = TeacherForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = PeopleService().add_teacher(school, by=request.user, **form.cleaned_data)
        messages.success(request, f"Teacher added. Username: {user.username}")
        return redirect("schools:teacher_list")
    teachers = User.objects.filter(school=school, role="teacher")
    return render(request, "schools/teacher_list.html", {"teachers": teachers, "form": form, "school": school})


@admin_only
def student_import(request):
    """CSV import: preview first, then import."""
    school = _my_school(request)
    form = CsvImportForm(request.POST or None, request.FILES or None)
    result, preview = None, False
    if request.method == "POST" and form.is_valid():
        commit = request.POST.get("step") == "import"
        result = PeopleService().import_csv(school, form.cleaned_data["file"], request.user, commit=commit)
        preview = not commit
        if commit:
            messages.success(request, f"{len(result.added)} students imported, {len(result.errors)} rows skipped.")
    return render(request, "schools/student_import.html", {"form": form, "result": result, "preview": preview})


@admin_only
def csv_template(request):  # pylint: disable=unused-argument
    response = HttpResponse("first_name,last_name,section,password,family_consent,parent_email\n"
                            "Aroha,Smith,7A,Kiaora@2026,yes,parent@example.com\n", content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="cyberquest_students_template.csv"'
    return response
