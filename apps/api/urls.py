"""urls.py - /api/ URLs: JSON endpoints (v1) and the API check page."""

from django.urls import path

from . import endpoints, views

app_name = "api"
urlpatterns = [
    path("check/", views.api_check, name="check"),
    path("v1/", endpoints.IndexApi.as_view(), name="index"),
    path("v1/health/", endpoints.HealthApi.as_view(), name="health"),
    path("v1/levels/", endpoints.LevelsApi.as_view(), name="levels"),
    path("v1/plans/", endpoints.PlansApi.as_view(), name="plans"),
    path("v1/team/", endpoints.TeamApi.as_view(), name="team"),
    path("v1/meeting-photos/", endpoints.MeetingPhotosApi.as_view(), name="meeting_photos"),
    path("v1/integrations/", endpoints.IntegrationStatusApi.as_view(), name="integrations"),
    path("v1/integrations/<slug:provider>/test/", endpoints.IntegrationTestApi.as_view(), name="integration_test"),
]
