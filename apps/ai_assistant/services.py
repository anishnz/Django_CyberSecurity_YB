"""
services.py - Ask the AI for drafts, approve them, publish questions, explain pages
===================================================================================

Owner: Anish Shrestha (task A-20)

* The AI provider comes from IntegrationService().ai() – Claude, OpenAI or Gemini
  when a key is switched on, otherwise the offline template helper.
* Privacy: names and email addresses are removed from what we send (NFR-04).
* Two approvals: teacher (facts) + Cultural Guide when Māori content is found.
"""

from __future__ import annotations

import re

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.core.exceptions import AccessDeniedError, IntegrationError, ValidationError
from apps.core.services import AuditService
from apps.integrations.services import IntegrationService
from apps.learning.services import QuestionService

from .models import AIDraft

User = get_user_model()
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
MAORI_HINTS = re.compile(
    r"[āēīōūĀĒĪŌŪ]|\b(kia ora|whānau|whanau|tikanga|te reo|marae|kaiako|ākonga|akonga|aroha|"
    r"mana|tapu|kaitiaki|whakapapa)\b",
    re.IGNORECASE,
)
PROMPTS = {
    AIDraft.QUESTION: (
        "Write ONE multiple-choice QUESTION for New Zealand students (Level {level}).\n"
        "Use exactly this format:\nQuestion: ...\nA: ...\nB: ...\nC: ...\nD: ...\nAnswer: <letter>\n"
        "Feedback: one or two sentences that teach the safe choice.\nTOPIC: {topic}"
    ),
    AIDraft.TIP: "Write one short cyber-safety tip (2-3 sentences) for children aged 10-13.\nTOPIC: {topic}",
    AIDraft.PARENT: (
        "Write a short, friendly message (under 120 words) to parents and whānau about what their child "
        "is learning in CyberQuest and one thing to talk about at home.\nTOPIC: {topic}"
    ),
    AIDraft.EXPLAIN: (
        "Explain this cyber-safety idea in simple words for a 10-year-old (under 100 words).\nTOPIC: {topic}"
    ),
}
MAX_EXPLAINS_PER_HOUR = 20


def scrub(text: str) -> str:
    """Remove email addresses and real user names before text goes to an AI service."""
    text = EMAIL_RE.sub("[email]", text or "")
    names = {n for n in User.objects.filter(is_active=True).values_list("first_name", flat=True) if n and len(n) > 2}
    for name in sorted(names, key=len, reverse=True):
        text = re.sub(rf"\b{re.escape(name)}\b", "[name]", text)
    return text


def parse_question(text: str) -> dict:
    """Read 'Question / A-D / Answer / Feedback' text into the data QuestionFactory needs."""
    fields, options = {}, {}
    for line in (text or "").splitlines():
        m = re.match(r"^\s*(Question|Answer|Feedback|[A-D])\s*[:).]\s*(.+)$", line.strip(), re.IGNORECASE)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if len(key) == 1:
            options[key.upper()] = value
        else:
            fields[key.lower()] = value
    answer = (fields.get("answer") or "")[:1].upper()
    if not fields.get("question") or len(options) < 2 or answer not in options or not fields.get("feedback"):
        raise ValidationError(
            "The draft is not in the question format (Question, A–D, Answer, Feedback). Please edit it."
        )
    return {"text": fields["question"][:400], "options": options, "answer": answer, "feedback": fields["feedback"]}


class AIDraftService:
    """Make, approve and publish AI drafts."""

    @staticmethod
    def visible_to(user):
        qs = AIDraft.objects.select_related("topic", "created_by", "teacher_approved_by", "cultural_approved_by")
        if user.is_super_admin:
            return qs
        return qs.filter(school_id=user.school_id)

    @transaction.atomic
    def create(self, user, kind: str, request_text: str, topic=None) -> AIDraft:
        """Ask the AI (or the offline helper) for a draft. Names are removed first."""
        if not (user.is_teacher or user.is_super_admin or getattr(user, "is_cultural_guide", False)):
            raise AccessDeniedError("Only teachers can ask the AI for drafts.")
        request_text = (request_text or "").strip()[:300]
        subject = request_text or (topic.title if topic else "")
        if len(subject) < 3:
            raise ValidationError("Please write what the draft is about (or choose a topic).")
        if kind not in PROMPTS:
            raise ValidationError("Please choose a kind of draft.")
        level = topic.level.number if topic else 1
        prompt = PROMPTS[kind].format(level=level, topic=scrub(subject))
        ai = IntegrationService().ai()
        try:
            text = ai.generate(prompt, max_tokens=450)
        except IntegrationError as exc:
            raise ValidationError(
                f"The AI service did not answer ({exc.message}). Try again or use the offline helper."
            ) from exc
        draft = AIDraft.objects.create(
            kind=kind,
            topic=topic,
            request_text=subject,
            text=text[:4000],
            provider=ai.label,
            needs_cultural_check=bool(MAORI_HINTS.search(text)),
            created_by=user,
            school=user.school,
        )
        AuditService.log(user, "ai_draft_created", f"draft {draft.pk}", new=ai.label)
        return draft

    @staticmethod
    def edit(user, draft: AIDraft, text: str, needs_cultural: bool) -> None:
        """Save the teacher's changes; the approvals start again."""
        if draft.status in (AIDraft.PUBLISHED,):
            raise ValidationError("A published draft cannot be changed.")
        draft.text = text.strip()[:4000]
        draft.needs_cultural_check = needs_cultural or bool(MAORI_HINTS.search(draft.text))
        # Any change means the people must look again.
        draft.teacher_approved_by = draft.cultural_approved_by = None
        draft.status = AIDraft.DRAFT
        draft.save()
        AuditService.log(user, "ai_draft_edited", f"draft {draft.pk}")

    @staticmethod
    def approve(user, draft: AIDraft, as_role: str) -> AIDraft:
        """Give the teacher or cultural approval; both done means 'approved'."""
        if draft.status not in (AIDraft.DRAFT,):
            raise ValidationError("Only drafts waiting for approval can be approved.")
        if as_role == "teacher":
            if not (user.is_teacher or user.is_super_admin or user.is_school_admin):
                raise AccessDeniedError("Only a teacher can give the teacher approval.")
            draft.teacher_approved_by = user
        elif as_role == "cultural":
            if not getattr(user, "is_cultural_guide", False):
                raise AccessDeniedError("Only a Cultural Guide (Kaiārahi) can give the cultural approval.")
            draft.cultural_approved_by = user
        else:
            raise ValidationError("Unknown approval.")
        if draft.teacher_ok and draft.cultural_ok:
            draft.status = AIDraft.APPROVED
        draft.save()
        AuditService.log(user, f"ai_draft_{as_role}_approved", f"draft {draft.pk}", new=draft.status)
        return draft

    @staticmethod
    def reject(user, draft: AIDraft, note: str) -> None:
        """Reject a draft with a short reason."""
        if len((note or "").strip()) < 3:
            raise ValidationError("Please write why (a few words).")
        draft.status, draft.review_note = AIDraft.REJECTED, note.strip()[:300]
        draft.save()
        AuditService.log(user, "ai_draft_rejected", f"draft {draft.pk}", details=note)

    @transaction.atomic
    def publish_question(self, user, draft: AIDraft):
        """Approved question draft → a practice question for the school."""
        if draft.kind != AIDraft.QUESTION or draft.status != AIDraft.APPROVED:
            raise ValidationError("Only approved question drafts can become practice questions.")
        if draft.topic is None:
            raise ValidationError("Please choose a topic for the draft first.")
        data = parse_question(draft.text)
        data.update(level=draft.topic.level.number, category=draft.topic.category, topic=draft.topic.code)
        author = user if user.is_teacher else draft.created_by
        if author is None or not author.is_teacher:
            raise AccessDeniedError("A teacher publishes practice questions for their school.")
        question = QuestionService().save(data, "single", author)
        question.topic_code = draft.topic.code
        question.save(update_fields=["topic_code"])
        draft.question, draft.status = question, AIDraft.PUBLISHED
        draft.save()
        return question


class PageHelper:
    """'Explain this page': the help article first, then a short AI answer."""

    @staticmethod
    def answer(view_name: str, role: str, question: str) -> tuple[str, object]:
        """Answer a question about a page from its help article (AI when a key is on)."""
        from apps.helpcentre.services import HelpService  # pylint: disable=import-outside-toplevel

        article = HelpService.for_page(view_name, role)
        question = scrub(question.strip()[:300])
        if not question:
            return "", article
        context = (
            f"{article.title}: {article.summary}\n{article.body}" if article else "CyberQuest school learning app."
        )
        prompt = (
            f"You are the help assistant inside CyberQuest. Answer in 2-4 short sentences using ONLY this guide. "
            f"If the guide does not cover it, say so and suggest the Help centre or a ticket.\nGUIDE:\n{context}\n"
            f"QUESTION: {question}"
        )
        ai = IntegrationService().ai()
        if ai.provider == "offline":
            return (
                f"Here is the guide for this page: {article.summary}"
                if article
                else "There is no guide for this page yet. Please open the Help centre or create a ticket."
            ), article
        try:
            return ai.generate(prompt, max_tokens=250), article
        except IntegrationError:
            return (article.summary if article else "The helper is not available right now."), article
