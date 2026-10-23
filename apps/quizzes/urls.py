"""urls.py - /quiz/ URLs."""
from django.urls import path

from . import views

app_name = "quizzes"
urlpatterns = [
    path("", views.student_dashboard, name="student_dashboard"),
    path("level/<int:number>/", views.level_page, name="level"),
    path("topic/<str:code>/", views.topic_page, name="topic"),
    path("practice/start/", views.practice_start, name="practice_start"),
    path("exam/start/", views.exam_start, name="exam_start"),
    path("session/<int:pk>/", views.question, name="question"),
    path("session/<int:pk>/answer/", views.answer, name="answer"),
    path("session/<int:pk>/feedback/", views.feedback, name="feedback"),
    path("session/<int:pk>/result/", views.result, name="result"),
    path("my-results/", views.my_results, name="my_results"),
    path("teacher/", views.teacher_dashboard, name="teacher_dashboard"),
    path("teacher/assignments/", views.assignment_list, name="assignment_list"),
    path("teacher/assignments/<int:pk>/delete/", views.assignment_delete, name="assignment_delete"),
    path("guest/try/", views.guest_try, name="guest_try"),
]
