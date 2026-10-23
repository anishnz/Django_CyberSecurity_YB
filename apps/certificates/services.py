"""
services.py - Issue certificates and draw the PDF (A4 landscape, QR code)
=========================================================================

Owner: Dinesh Upreti (task D-16)
"""
from __future__ import annotations

import io
import zipfile

from django.conf import settings
from django.db import transaction

from .models import Certificate


class CertificateService:
    """Issue, draw and bundle certificates."""

    @transaction.atomic
    def issue_for(self, session) -> Certificate | None:
        """Called by QuizService when an exam is passed. Keeps the best score."""
        if not session.passed or session.mode != "exam":
            return None
        student = session.student
        cert, created = Certificate.objects.get_or_create(student=student, level=session.level, defaults={
            "session": session, "student_name": student.get_full_name() or student.username,
            "school_name": student.school.name if student.school else "", "percentage": session.percentage,
            "awareness_level": session.awareness_level})
        if not created and session.percentage > cert.percentage:
            cert.session, cert.percentage, cert.awareness_level = session, session.percentage, session.awareness_level
            cert.save()
        return cert

    @staticmethod
    def pdf(cert: Certificate, verify_url: str) -> bytes:
        # pylint: disable=import-outside-toplevel
        from reportlab.graphics import renderPDF
        from reportlab.graphics.barcode.qr import QrCodeWidget
        from reportlab.graphics.shapes import Drawing
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.pdfgen import canvas
        from apps.core.pdf import register_fonts
        regular, bold = register_fonts()
        width, height = landscape(A4)
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=landscape(A4))
        c.setTitle(f"CyberQuest certificate {cert.code}")
        harbour, kowhai = colors.HexColor("#0E3B43"), colors.HexColor("#F2B705")
        c.setFillColor(colors.HexColor("#F6F8F8"))
        c.rect(0, 0, width, height, fill=1, stroke=0)
        c.setStrokeColor(harbour)
        c.setLineWidth(6)
        c.rect(24, 24, width - 48, height - 48)
        c.setStrokeColor(kowhai)
        c.setLineWidth(2)
        c.rect(36, 36, width - 72, height - 72)
        c.setFillColor(harbour)
        c.setFont(bold, 34)
        c.drawCentredString(width / 2, height - 110, "Certificate of Achievement")
        c.setFont(regular, 16)
        c.drawCentredString(width / 2, height - 138, "Tohu Paetae")
        c.setFont(regular, 15)
        c.drawCentredString(width / 2, height - 190, "This certifies that")
        c.setFont(bold, 30)
        c.drawCentredString(width / 2, height - 232, cert.student_name)
        c.setFont(regular, 15)
        if cert.school_name:
            c.drawCentredString(width / 2, height - 258, f"of {cert.school_name}")
        c.drawCentredString(width / 2, height - 300, f"passed CyberQuest Level {cert.level.number}: {cert.level.name}")
        c.setFont(bold, 18)
        c.drawCentredString(width / 2, height - 332, f"Score {cert.percentage:.0f}%  ·  {cert.awareness_level}")
        c.setFont(regular, 11)
        c.setFillColor(colors.HexColor("#5B6E72"))
        c.drawString(70, 80, f"Issued {cert.issued_at:%d %B %Y}  ·  Certificate code {cert.code}")
        c.drawString(70, 64, f"{settings.PROJECT['company']} – {settings.PROJECT['tagline']}")
        c.drawString(70, 48, "Check this certificate: scan the QR code or visit the verify link.")
        qr = QrCodeWidget(verify_url)
        x1, y1, x2, y2 = qr.getBounds()
        size = 92
        drawing = Drawing(size, size, transform=[size / (x2 - x1), 0, 0, size / (y2 - y1), 0, 0])
        drawing.add(qr)
        renderPDF.draw(drawing, c, width - 70 - size, 44)
        c.showPage()
        c.save()
        return buf.getvalue()

    def zip_for(self, certificates, url_for) -> bytes:
        """All certificates for a section in one ZIP (teacher download)."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for cert in certificates:
                safe = "".join(ch for ch in cert.student_name if ch.isalnum() or ch in " -").strip().replace(" ", "_")
                zf.writestr(f"Level{cert.level.number}_{safe}_{cert.code}.pdf", self.pdf(cert, url_for(cert)))
        return buf.getvalue()
