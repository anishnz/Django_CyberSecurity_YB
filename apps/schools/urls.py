"""urls.py - /schools/ URLs."""

from django.urls import path

from . import views

app_name = "schools"
urlpatterns = [
    path("", views.school_list, name="school_list"),
    path("new/", views.school_new, name="school_new"),
    path("<int:pk>/", views.school_detail, name="school_detail"),
    path("<int:pk>/rename/", views.school_rename, name="school_rename"),
    path("<int:pk>/status/", views.school_status, name="school_status"),
    path("sections/<int:pk>/capacity/", views.section_capacity, name="section_capacity"),
    path("my/", views.admin_dashboard, name="admin_dashboard"),
    path("my/classes/", views.class_list, name="class_list"),
    path("my/students/", views.student_list, name="student_list"),
    path("my/students/new/", views.student_new, name="student_new"),
    path("my/students/<int:pk>/", views.student_edit, name="student_edit"),
    path("my/students/import/", views.student_import, name="student_import"),
    path("my/students/template.csv", views.csv_template, name="csv_template"),
    path("my/people/<int:pk>/toggle/", views.person_toggle, name="person_toggle"),
    path("my/teachers/", views.teacher_list, name="teacher_list"),
]
