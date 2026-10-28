"""
views.py - Public website pages (no login needed) and the Demo Guest tour
=========================================================================

Owner: Dinesh Upreti (public website)
Pages: Home (slider + video), Features, Levels, Pricing, Te Tiriti and community,
About us, Team, Contact us, FAQ, Privacy. "Try as Demo Guest" logs in as the
read-only demo account.

Website content page (Super Admin): upload team photos and meeting photos.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.decorators import super_admin_required
from apps.core.exceptions import AccessDeniedError, UploadRejectedError
from apps.core.models import SystemSettings
from apps.licensing.plans import LEVEL_PACK_PRICES, PLAN_CLASSES
from apps.medialib.youtube import safe_embed_url
from apps.security.services import SecurityLog

from . import business, content, story
from .forms import ContactForm, MeetingPhotoForm, TeamMemberForm
from .models import MeetingPhoto, Slide, TeamMember
from .services import WebsiteContentService

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
    return render(
        request,
        "website/pricing.html",
        {
            "plans": plans,
            "packs": LEVEL_PACK_PRICES,
            "rows": business.price_table(),
            "pack_total": business.level_pack_total(),
        },
    )


# --------------------------------------------------------------------------- Business pages (Dinesh, Rajneesh)
def discount(request):
    """How a kura or small rural school gets the 50% community discount."""
    return render(request, "website/discount.html", {"b": business, "rows": business.price_table()})


def business_case(request):
    """How CyberQuest pays its own way, and how it is different from other products."""
    model = business.SustainabilityModel(business.RUNNING_COSTS)
    return render(request, "website/business.html", {"b": business, "model": model})


def swot(request):
    return render(request, "website/swot.html", {"b": business})


def proposal(request):
    return render(
        request,
        "website/proposal.html",
        {"p": business.PROPOSAL, "total": business.proposal_total(), "total_gst": business.BUILD_COST_GST},
    )


def contract(request):
    """A sample service agreement (template only, not legal advice)."""
    return render(request, "website/contract.html", {"b": business, "rows": business.price_table()})


def community(request):
    return render(request, "website/community.html")


def about(request):
    """About us: our team (with photos) and the meetings slider."""
    service = WebsiteContentService()
    return render(request, "website/about.html", {"team": service.team(), "meeting_photos": service.meeting_photos()})


def our_story(request):
    """Our project story: a simulated case study, our Māori community friends and their proposals."""
    service = WebsiteContentService()
    return render(request, "website/story.html", {"s": story, "meeting_photos": service.meeting_photos()})


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


# --------------------------------------------------------------------------- Website content (Super Admin)
@super_admin_required
def manage(request):
    """Website content page: team photos and bios, meeting photos for the slider."""
    members = [(m, TeamMemberForm(initial={"bio": m.bio}, prefix=f"m{m.pk}")) for m in TeamMember.objects.all()]
    return render(
        request,
        "website/manage.html",
        {"members": members, "photo_form": MeetingPhotoForm(), "photos": MeetingPhoto.objects.all()},
    )


@super_admin_required
@require_POST
def manage_member(request, pk):
    """Save one team member's bio and/or new photo."""
    member = get_object_or_404(TeamMember, pk=pk)
    form = TeamMemberForm(request.POST, request.FILES, prefix=f"m{member.pk}")
    service = WebsiteContentService(request.user, request)
    if request.POST.get("remove_photo"):
        service.remove_member_photo(member)
        messages.info(request, f"Photo removed for {member.name}.")
    elif form.is_valid():
        try:
            service.update_member(member, bio=form.cleaned_data["bio"], photo=form.cleaned_data["photo"])
            messages.success(request, f"Saved {member.name}.")
        except UploadRejectedError as exc:
            messages.error(request, exc.message)
    else:
        messages.error(request, "Please upload a JPG, PNG or WebP picture.")
    return redirect(f"{reverse('website:manage')}#team-{member.pk}")


@super_admin_required
@require_POST
def manage_photo_add(request):
    """Upload one meeting photo."""
    form = MeetingPhotoForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            WebsiteContentService(request.user, request).add_meeting_photo(form)
            messages.success(request, "Meeting photo added to the slider.")
        except UploadRejectedError as exc:
            messages.error(request, exc.message)
    else:
        messages.error(request, "Please add a title and a JPG, PNG or WebP photo.")
    return redirect(f"{reverse('website:manage')}#meetings")


@super_admin_required
@require_POST
def manage_photo_action(request, pk, action):
    """Show/hide or delete one meeting photo."""
    photo = get_object_or_404(MeetingPhoto, pk=pk)
    service = WebsiteContentService(request.user, request)
    if action == "toggle":
        service.toggle_meeting_photo(photo)
        messages.info(request, f"'{photo.title}' is now {'shown' if photo.is_active else 'hidden'}.")
    elif action == "delete":
        service.delete_meeting_photo(photo)
        messages.info(request, "Meeting photo deleted.")
    return redirect(f"{reverse('website:manage')}#meetings")
