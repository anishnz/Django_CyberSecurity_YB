"""urls.py - /reports/ URLs."""
from django.urls import path

from . import views

app_name = "reports"
urlpatterns = [
    path("bi/", views.bi_dashboard, name="bi_dashboard"),
    path("school/", views.school_bi, name="school_bi"),
    path("class/", views.class_report_pick, name="class_report_pick"),
    path("class/<int:pk>/", views.class_report, name="class_report"),
    path("student/<int:pk>/", views.student_report, name="student_report"),
]
