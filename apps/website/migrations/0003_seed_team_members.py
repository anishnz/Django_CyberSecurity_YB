"""Create the four team members from settings.PROJECT (names, IDs, roles). Photos are uploaded later."""

from django.conf import settings
from django.db import migrations


def add_team(apps, schema_editor):  # pylint: disable=unused-argument
    TeamMember = apps.get_model("website", "TeamMember")
    for order, (name, sid, role) in enumerate(settings.PROJECT["team"], start=1):
        TeamMember.objects.get_or_create(name=name, defaults={"student_id": sid, "role": role, "order": order})


def remove_team(apps, schema_editor):  # pylint: disable=unused-argument
    apps.get_model("website", "TeamMember").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("website", "0002_team_and_meeting_photos")]
    operations = [migrations.RunPython(add_team, remove_team)]
