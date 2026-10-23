"""
roles.py - One class per user role (polymorphism instead of if/else chains)
===========================================================================

Owner: Anish Shrestha (task A-07)

Concepts:
    * Abstraction: ``Role`` is an abstract base class. It says WHAT every role must
      tell us (dashboard, menu, permissions) but not HOW.
    * Inheritance + polymorphism: SuperAdminRole, SchoolAdminRole, TeacherRole,
      StudentRole and GuestRole each answer differently. Code simply calls
      ``user.role_obj.dashboard_url`` without checking the role name.
    * Factory: ``role_for(code)`` returns the right Role object.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Role(ABC):
    """What every role must provide."""

    code = ""
    label = ""            # English (Māori)
    icon = "person"
    can_manage_users = False
    can_manage_school = False
    can_teach = False
    can_learn = False
    read_only = False

    @property
    @abstractmethod
    def dashboard_url(self) -> str:
        """URL name of this role's home dashboard."""

    @abstractmethod
    def menu(self) -> list[tuple[str, str, str]]:
        """Navigation items: (label, url name, icon)."""

    def __str__(self) -> str:
        return self.label


class SuperAdminRole(Role):
    """Company administrator: controls every school and setting."""

    code, label, icon = "super_admin", "Super Admin", "shield-lock"
    can_manage_users = can_manage_school = True

    @property
    def dashboard_url(self) -> str:
        return "core:super_dashboard"

    def menu(self):
        return [("Dashboard (Papatohu)", "core:super_dashboard", "speedometer2"),
                ("Schools (Kura)", "schools:school_list", "building"),
                ("Users", "accounts:user_list", "people"),
                ("Licences", "licensing:licence_list", "patch-check"),
                ("Payments", "payments:payment_list", "cash-coin"),
                ("Content (Ako)", "learning:level_list", "journal-text"),
                ("Tickets", "helpdesk:ticket_list", "life-preserver"),
                ("BI", "reports:bi_dashboard", "graph-up"),
                ("System", "core:system", "gear")]


class SchoolAdminRole(Role):
    """Runs one school: classes, sections, students, teachers, licence."""

    code, label, icon = "school_admin", "School Admin", "building"
    can_manage_school = True

    @property
    def dashboard_url(self) -> str:
        return "schools:admin_dashboard"

    def menu(self):
        return [("Dashboard (Papatohu)", "schools:admin_dashboard", "speedometer2"),
                ("Classes (Akomanga)", "schools:class_list", "diagram-3"),
                ("Students (Ākonga)", "schools:student_list", "mortarboard"),
                ("Teachers (Kaiako)", "schools:teacher_list", "person-badge"),
                ("Licence", "licensing:my_licence", "patch-check"),
                ("Reports (Pūrongo)", "reports:school_bi", "graph-up"),
                ("Bulk email", "emails:bulk", "send"),
                ("Tickets", "helpdesk:ticket_list", "life-preserver")]


class TeacherRole(Role):
    """Assigns exams, writes practice questions, reads class reports."""

    code, label, icon = "teacher", "Teacher (Kaiako)", "person-badge"
    can_teach = True

    @property
    def dashboard_url(self) -> str:
        return "quizzes:teacher_dashboard"

    def menu(self):
        return [("Dashboard (Papatohu)", "quizzes:teacher_dashboard", "speedometer2"),
                ("Assignments", "quizzes:assignment_list", "calendar-check"),
                ("My questions", "learning:my_questions", "patch-question"),
                ("AI drafts", "ai_assistant:draft_list", "stars"),
                ("Media", "medialib:media_list", "collection-play"),
                ("Reports (Pūrongo)", "reports:class_report_pick", "bar-chart"),
                ("Tickets", "helpdesk:ticket_list", "life-preserver")]


class StudentRole(Role):
    """Studies topics, practises, sits exams, earns badges and certificates."""

    code, label, icon = "student", "Student (Ākonga)", "mortarboard"
    can_learn = True

    @property
    def dashboard_url(self) -> str:
        return "quizzes:student_dashboard"

    def menu(self):
        return [("My levels", "quizzes:student_dashboard", "signpost-split"),
                ("My results", "quizzes:my_results", "bar-chart"),
                ("Certificates", "certificates:my_certificates", "award"),
                ("Help (Āwhina)", "helpdesk:ticket_list", "life-preserver")]


class GuestRole(Role):
    """Read-only Demo Guest for open days."""

    code, label, icon = "guest", "Demo Guest", "eye"
    read_only = True

    @property
    def dashboard_url(self) -> str:
        return "website:guest_tour"

    def menu(self):
        return [("Demo tour", "website:guest_tour", "compass"),
                ("Try a quiz", "quizzes:guest_try", "controller")]


ROLE_CLASSES = {cls.code: cls for cls in (SuperAdminRole, SchoolAdminRole, TeacherRole, StudentRole, GuestRole)}
ROLE_CHOICES = [(code, cls.label) for code, cls in ROLE_CLASSES.items()]


def role_for(code: str) -> Role:
    """Factory: return the Role object for a role code (unknown codes become Guest)."""
    return ROLE_CLASSES.get(code, GuestRole)()
