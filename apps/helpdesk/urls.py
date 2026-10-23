"""urls.py - /tickets/ URLs."""

from django.urls import path

from . import views

app_name = "helpdesk"
urlpatterns = [
    path("", views.ticket_list, name="ticket_list"),
    path("new/", views.ticket_new, name="ticket_new"),
    path("<int:pk>/", views.ticket_detail, name="ticket_detail"),
    path("<int:pk>/move/", views.ticket_move, name="ticket_move"),
    path("<int:pk>/assign/", views.ticket_assign, name="ticket_assign"),
    path("report-question/<int:question_pk>/", views.report_question, name="report_question"),
]
