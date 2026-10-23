"""views.py - My certificates, PDF download, public verify page, section ZIP. Owner: Dinesh Upreti."""
from __future__ import annotations

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.accounts.decorators import role_required
from apps.core.exceptions import AccessDeniedError
from apps.schools.models import Section

from .models import Certificate
from .services import CertificateService


def _verify_url(request, cert) -> str:
    return request.build_absolute_uri(reverse("certificates:verify", args=[cert.code]))


@role_required("student")
def my_certificates(request):
    """Student's certificates with free share links (only the verify link is shared – first name only)."""
    from apps.integrations.adapters import ShareLinks  # pylint: disable=import-outside-toplevel
    certs = Certificate.objects.filter(student=request.user, is_revoked=False).select_related("level")
    shares = {}
    for c in certs:
        url = _verify_url(request, c)
        text = f"I passed CyberQuest Level {c.level.number}! Check my certificate: {url}"
        shares[c.code] = {"whatsapp": ShareLinks.whatsapp(text), "viber": ShareLinks.viber(text),
                          "facebook": ShareLinks.facebook(url)}
    return render(request, "certificates/my_certificates.html", {"certs": certs, "shares": shares})


@role_required("student", "teacher", "school_admin", "super_admin")
def download(request, code):
    cert = get_object_or_404(Certificate.objects.select_related("level", "student"), code=code, is_revoked=False)
    user = request.user
    if not (user.pk == cert.student_id or user.is_super_admin or
            (user.role in ("teacher", "school_admin") and user.school_id == cert.student.school_id)):
        raise AccessDeniedError("This certificate belongs to another student.")
    response = HttpResponse(CertificateService.pdf(cert, _verify_url(request, cert)), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="CyberQuest_Level{cert.level.number}_{cert.code}.pdf"'
    return response


def verify(request, code):
    """Public: anyone with the code (or QR) can check the certificate is real. Shows first name only."""
    cert = Certificate.objects.select_related("level").filter(code=code.upper()).first()
    return render(request, "certificates/verify.html", {"cert": cert, "code": code,
                  "first_name": cert.student_name.split()[0] if cert else ""})


@role_required("teacher", "school_admin", "super_admin")
def section_zip(request, pk):
    qs = Section.objects.all() if request.user.is_super_admin else Section.objects.filter(school_class__school=request.user.school)
    section = get_object_or_404(qs, pk=pk)
    certs = Certificate.objects.filter(student__student_profile__section=section, is_revoked=False).select_related("level")
    data = CertificateService().zip_for(certs, lambda c: _verify_url(request, c))
    response = HttpResponse(data, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="certificates_section_{section.pk}.zip"'
    return response
