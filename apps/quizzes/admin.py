"""admin.py - Django admin for quizzes."""
from django.contrib import admin

from .models import Assignment, Badge, QuizSession

admin.site.register([Assignment, QuizSession, Badge])
