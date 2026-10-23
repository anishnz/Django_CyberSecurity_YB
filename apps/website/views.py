"""
views.py - Public website pages (no login needed) and the Demo Guest tour
=========================================================================

Owner: Dinesh Upreti (public website)
Pages: Home (slider + video), Features, Levels, Pricing, Te Tiriti and community,
About us, Team, Contact us, FAQ, Privacy. "Try as Demo Guest" logs in as the
read-only demo account.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.core.exceptions import AccessDeniedError
from apps.core.models import SystemSettings
from apps.licensing.plans import LEVEL_PACK_PRICES, PLAN_CLASSES
from apps.medialib.youtube import safe_embed_url
from apps.security.services import SecurityLog

from . import content
from .forms import ContactForm
from .models import Slide

User = get_user_model()

DEFAULT_SLIDES = [
    {
        "title": "Learn. Play. Decide.",
        "caption": "Short, game-style lessons that help tamariki stay safe online.",
        "static_image": "img/slides/slide1.svg",
    },
    {
        "title": "Built with our community",
        "caption": "English first, with te reo Māori in brackets. Checked by our Kaiārahi.",
        "static_image": "img/slides/slide2.svg",
    },
    {
        "title": "Reports teachers can use",
        "caption": "Kind, simple reports for every class – never the word 'Fail'.",
        "static_image": "img/slides/slide3.svg",
    },
]

FEATURES = [
    ("signpost-split", "Six learning levels", "From Cyber Starter (Year 7) to Cyber Pro (adults)."),
    ("controller", "Practice and exams", "Instant feedback in practice; a 20-question exam for each level."),
    ("award", "Badges and certificates", "PDF certificates with a QR code anyone can check."),
    ("people", "Roles for everyone", "Super Admin, School Admin, Teacher (Kaiako), Student (Ākonga), Demo Guest."),
    ("graph-up", "Reports and BI", "Class reports, school charts and business performance."),
    ("life-preserver", "Help desk", "Tickets for questions and problems, with email updates."),
    ("envelope", "Email to whānau", "Templates for parents and teachers, with unsubscribe."),
    ("shield-lock", "Strong security", "Two-step login, security log, encrypted keys, lockout."),
    ("stars", "AI helper", "Short text drafts – always checked by a teacher and the Kaiārahi."),
]


def _slides():
    rows = list(Slide.objects.filter(is_active=True))
    return rows or DEFAULT_SLIDES


def home(request):
    cfg = SystemSettings.load()
    return render(
        request,
        "website/home.html",
        {"slides": _slides(), "c": content, "video_url": safe_embed_url(cfg.welcome_video_url)},
    )


def features(request):
    return render(request, "website/features.html", {"features": FEATURES})


def levels(request):
    from apps.learning.models import Level  # pylint: disable=import-outside-toplevel

    return render(request, "website/levels.html", {"levels": Level.objects.prefetch_related("topics")})


def pricing(request):
    plans = [cls(None, None) for cls in PLAN_CLASSES.values()]
    return render(request, "website/pricing.html", {"plans": plans, "packs": LEVEL_PACK_PRICES})


def community(request):
    return render(request, "website/community.html")


def about(request):
    return render(request, "website/about.html")


def faq(request):
    return render(request, "website/faq.html")


def privacy(request):
    return render(request, "website/privacy.html")


def contact(request):
    """Contact us: saves the message and opens a help desk ticket."""
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        msg = form.save()
        try:
            from apps.helpdesk.services import TicketService  # pylint: disable=import-outside-toplevel

            ticket = TicketService().from_contact(msg)
            msg.ticket_number = ticket.number
            msg.save(update_fields=["ticket_number"])
            messages.success(
                request, f"Ngā mihi (thank you)! Your message is ticket {ticket.number}. We will reply by email."
            )
        except ImportError:
            messages.success(request, "Ngā mihi (thank you)! We will reply by email.")
        return redirect("website:contact")
    cfg = SystemSettings.load()
    return render(request, "website/contact.html", {"form": form, "cfg": cfg})


@require_POST
def guest_login(request):
    """Log in as the read-only Demo Guest."""
    if not settings.DEMO_MODE:
        raise AccessDeniedError("Demo Guest is switched off.")
    guest = User.objects.filter(role="guest", is_active=True).first()
    if guest is None:
        raise AccessDeniedError("There is no Demo Guest account. Run: python manage.py seed_demo")
    login(request, guest, backend="django.contrib.auth.backends.ModelBackend")
    SecurityLog.record("login", request, guest, details="demo guest")
    messages.info(request, "You are exploring as Demo Guest. Nothing you do is saved.")
    return redirect("website:guest_tour")


@login_required
def guest_tour(request):
    from apps.learning.models import Level  # pylint: disable=import-outside-toplevel

    return render(request, "website/guest_tour.html", {"levels": Level.objects.prefetch_related("topics")})
