"""Correct Jihe Qi's student ID (271008116) in databases made before 31 Oct 2026."""

from django.db import migrations


def fix_id(apps, schema_editor):  # pylint: disable=unused-argument
    apps.get_model("website", "TeamMember").objects.filter(name="Jihe Qi", student_id="27008116").update(
        student_id="271008116"
    )


def undo(apps, schema_editor):  # pylint: disable=unused-argument
    apps.get_model("website", "TeamMember").objects.filter(name="Jihe Qi", student_id="271008116").update(
        student_id="27008116"
    )


class Migration(migrations.Migration):
    dependencies = [("website", "0003_seed_team_members")]
    operations = [migrations.RunPython(fix_id, undo)]
