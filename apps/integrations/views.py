"""
views.py - Integrations page, test connection and AI test page
==============================================================

Owner: Jihe Qi (tasks J-09, J-10, J-11, J-14). Super Admin only.

AI models page: switch models on, choose the default, set the order, and check
each model (or all of them) with one click. WhatsApp: send one test message.

Keys are typed into a password box, saved encrypted, and only ever shown masked
(for example ``sk-a…9Xz``). Every key change is written to the security log.
"""

from __future__ import annotations

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.decorators import super_admin_required
from apps.core.exceptions import IntegrationError, ValidationError

from .adapters import ADAPTERS, AI_ORDER, FallbackAIProvider, OfflineTemplateProvider
from .services import IntegrationService

MAX_PROMPT = 1500


@super_admin_required
def integration_list(request):
    """One card per service: status, masked key, settings, Test and Clear buttons."""
    return render(request, "integrations/list.html", {"cards": IntegrationService().cards()})


@super_admin_required
@require_POST
def integration_save(request, provider):
    """Save one integration card (key, settings, on/off)."""
    cls = ADAPTERS.get(provider)
    if cls is None:
        return redirect("integrations:list")
    extra = {k: request.POST.get(k, "") for k, _, _ in cls.extra_fields}
    IntegrationService().save(
        provider,
        secret=request.POST.get("secret", ""),
        extra=extra,
        enabled=request.POST.get("enabled") == "on",
        user=request.user,
        request=request,
    )
    messages.success(request, f"{cls.label} settings saved.")
    return redirect(f"/integrations/#{provider}")


def _say(request, label: str, ok: bool, msg: str) -> None:
    """Show a test result once: AI messages already start with the model name."""
    text = msg if msg.startswith(label) else f"{label}: {msg}"
    (messages.success if ok else messages.error)(request, text)


def _back(request, provider):
    """Go back to the AI models page or to the provider's card."""
    if request.POST.get("next") == "ai":
        return redirect("integrations:ai_models")
    return redirect(f"/integrations/#{provider}")


@super_admin_required
@require_POST
def integration_test(request, provider):
    """Test one service now. AI models get one tiny real question, so the answer proves tokens are left."""
    if provider not in ADAPTERS:
        return redirect("integrations:list")
    ok, msg = IntegrationService().test(provider)
    _say(request, ADAPTERS[provider].label, ok, msg)
    return _back(request, provider)


@super_admin_required
def ai_models(request):
    """AI models: on/off, default, order, and a Check button for each model."""
    service = IntegrationService()
    if request.method == "POST":
        try:
            order = {name: int(request.POST.get(f"order-{name}") or 50) for name in AI_ORDER}
            service.save_ai_settings(
                order=order,
                default=request.POST.get("default", ""),
                switched_on={name for name in AI_ORDER if request.POST.get(f"on-{name}") == "on"},
                user=request.user,
            )
            messages.success(
                request, "AI settings saved. Order: " + " → ".join(ADAPTERS[n].label for n in service.ai_order())
            )
        except (ValueError, ValidationError) as exc:
            messages.error(request, getattr(exc, "message", "Order numbers must be whole numbers from 1 to 99."))
        return redirect("integrations:ai_models")
    rows = service.ai_rows()
    has_default = any(r["row"] is not None and r["row"].is_default for r in rows)
    return render(request, "integrations/ai_models.html", {"rows": rows, "has_default": has_default})


@super_admin_required
@require_POST
def ai_check_all(request):
    """Check every AI model that has a key: a tiny real question to each one."""
    service = IntegrationService()
    checked = 0
    for name in service.ai_order():
        if service.enabled(name) or (service.row(name).has_secret):
            ok, msg = service.test(name)
            _say(request, service.adapter(name).label, ok, msg)
            checked += 1
    if not checked:
        messages.info(request, "No AI model has a key yet. Add a key on the Integrations page first.")
    return redirect("integrations:ai_models")


@super_admin_required
@require_POST
def whatsapp_test(request):
    """Send Meta's test template to one phone number."""
    try:
        message_id = IntegrationService().whatsapp_test(request.POST.get("phone", ""), user=request.user)
        messages.success(request, f"WhatsApp accepted the test message (id {message_id[:24] or 'not given'}).")
    except (ValidationError, IntegrationError) as exc:
        messages.error(request, exc.message)
    return redirect("/integrations/#whatsapp")


@super_admin_required
@require_POST
def integration_clear(request, provider):
    IntegrationService().clear(provider, request.user, request)
    messages.info(request, f"{ADAPTERS[provider].label} key removed and switched off.")
    return redirect(f"/integrations/#{provider}")


@super_admin_required
def ai_test(request):
    """Try a prompt against one AI provider (or the offline helper) and see the answer."""
    service = IntegrationService()
    choices = [
        ("auto", "Automatic (default first, then the next on failure)"),
        ("offline", OfflineTemplateProvider.label),
    ]
    choices += [(name, ADAPTERS[name].label) for name in service.ai_order()]
    ctx = {"choices": choices, "prompt": "", "provider": "auto", "answer": "", "error": "", "used": "", "attempts": []}
    if request.method == "POST":
        prompt = request.POST.get("prompt", "").strip()[:MAX_PROMPT]
        provider = request.POST.get("provider", "auto")
        ctx.update(prompt=prompt, provider=provider)
        ai = (
            service.ai()
            if provider == "auto"
            else (OfflineTemplateProvider() if provider == "offline" else service.adapter(provider))
        )
        ctx["used"] = ai.label
        if not prompt:
            ctx["error"] = "Please type a prompt."
        else:
            try:
                ctx["answer"] = ai.generate(prompt, max_tokens=300)
            except IntegrationError as exc:
                ctx["error"] = exc.message
            if isinstance(ai, FallbackAIProvider):
                ctx["attempts"], ctx["used"] = ai.attempts, ai.label
    return render(request, "integrations/ai_test.html", ctx)
