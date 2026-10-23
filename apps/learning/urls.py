"""urls.py - /learn/ URLs."""

from django.urls import path

from . import views

app_name = "learning"
urlpatterns = [
    path("levels/", views.level_list, name="level_list"),
    path("levels/<int:number>/", views.level_detail, name="level_detail"),
    path("import/", views.import_content, name="import_content"),
    path("my-questions/", views.my_questions, name="my_questions"),
    path("questions/new/", views.question_edit, name="question_new"),
    path("questions/<int:pk>/", views.question_edit, name="question_edit"),
    path("questions/<int:pk>/remove/", views.question_archive, name="question_archive"),
]
