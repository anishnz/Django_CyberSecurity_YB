"""test_media_access.py - Uploaded files are shown when DEBUG is off, but only to the right people.

Owner: Jihe Qi (QA). Tests run with DEBUG = False, the same as run.bat and run_local.bat.
"""

import pytest
from django.conf import settings
from django.test import Client

from apps.core.media import MediaAccessPolicy
from apps.helpdesk.models import TicketAttachment, TicketComment
from apps.helpdesk.services import TicketService

pytestmark = pytest.mark.django_db
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture(name="media")
def media_fixture(tmp_path, monkeypatch):
    """Use an empty media folder; media('a/b.png') writes a small file and returns its path."""
    monkeypatch.setattr(settings, "MEDIA_ROOT", tmp_path)

    def _write(rel: str) -> str:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(PNG)
        return rel

    return _write


def test_debug_is_off_in_tests_like_the_run_scripts():
    assert settings.DEBUG is False


def test_team_and_meeting_photos_are_public(media):
    for rel in (media("website/team/anish.png"), media("website/meetings/hui.png"), media("schools/logos/l.png")):
        response = Client().get(f"/media/{rel}")
        assert response.status_code == 200
        assert response["X-Content-Type-Options"] == "nosniff"


def test_payslips_are_never_served_by_url(media, login):
    rel = media("payslips/1/slip.png")
    assert Client().get(f"/media/{rel}").status_code == 404
    assert login("superadmin").get(f"/media/{rel}").status_code == 404  # only via the payments page


def test_unknown_folders_and_path_tricks_are_blocked(media):
    media("payslips/1/slip.png")
    for url in ("/media/secret.txt", "/media/website/../payslips/1/slip.png", "/media/other/x.png"):
        assert Client().get(url).status_code == 404
    assert MediaAccessPolicy().allows(None, "website/../payslips/1/slip.png") is False


def test_ticket_files_only_for_people_who_can_see_the_ticket(media, user, login):
    tama = user("tama.ngata")
    ticket = TicketService().create(title="Screen problem", description="My screen shows an error.", requester=tama)
    comment = TicketComment.objects.create(ticket=ticket, author=tama, body="Here is a screenshot.")
    rel = media(f"tickets/{ticket.number}/shot.png")
    TicketAttachment.objects.create(comment=comment, file=rel, original_name="shot.png", size_bytes=len(PNG))

    assert login("tama.ngata").get(f"/media/{rel}").status_code == 200
    assert login("sione.faleolo").get(f"/media/{rel}").status_code == 200  # teacher at the same school
    assert login("bikash.thapa").get(f"/media/{rel}").status_code == 404  # another school
    assert Client().get(f"/media/{rel}").status_code == 404  # not logged in
    assert login("tama.ngata").get(f"/media/{rel}")["Cache-Control"] == "private, no-store"


def test_internal_note_files_only_for_ticket_managers(media, user, login):
    tama, sione = user("tama.ngata"), user("sione.faleolo")
    ticket = TicketService().create(title="Screen problem", description="My screen shows an error.", requester=tama)
    note = TicketComment.objects.create(ticket=ticket, author=sione, body="Staff only.", is_internal=True)
    rel = media(f"tickets/{ticket.number}/note.png")
    TicketAttachment.objects.create(comment=note, file=rel, original_name="note.png", size_bytes=len(PNG))

    assert login("sione.faleolo").get(f"/media/{rel}").status_code == 200
    assert login("tama.ngata").get(f"/media/{rel}").status_code == 404


def test_library_file_without_a_record_is_hidden(media, login):
    rel = media("library/pdf/unknown.png")
    assert login("superadmin").get(f"/media/{rel}").status_code == 404


def test_library_file_waiting_for_cultural_check_is_hidden_from_students(media, user, login):
    from apps.medialib.models import MediaFile  # pylint: disable=import-outside-toplevel

    tama = user("tama.ngata")
    rel = media("library/image/marae.png")
    item = MediaFile.objects.create(
        kind="image", title="Marae", file=rel, school=tama.school, needs_cultural_check=True, cultural_check=False
    )
    assert login("sione.faleolo").get(f"/media/{rel}").status_code == 200  # teacher can check it
    assert login("tama.ngata").get(f"/media/{rel}").status_code == 404  # student waits for the Kaiārahi
    item.cultural_check = True
    item.save()
    assert login("tama.ngata").get(f"/media/{rel}").status_code == 200
    assert login("bikash.thapa").get(f"/media/{rel}").status_code == 404  # another school
