"""
views.py - Integrations page, test connection and AI test page
==============================================================

Owner: Jihe Qi (tasks J-09, J-10, J-11). Super Admin only.

Keys are typed into a password box, saved encrypted, and only ever shown masked
(for example ``sk-a…9Xz``). Every key change is written to the security log.
"""
from __future__ import annotations

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.decorators import super_admin_required
from apps.core.exceptions import IntegrationError

from .adapters import ADAPTERS, AI_ORDER, OfflineTemplateProvider
from .services import IntegrationService

MAX_PROMPT = 1500


@super_admin_required
def integration_list(request):
    """One card per service: status, masked key, settings, Test and Clear buttons."""
    return render(request, "integrations/list.html", {"cards": IntegrationService().cards()})


@super_admin_required
@require_POST
def integration_save(request, provider):
    cls = ADAPTERS.get(provider)
    if cls is None:
        return redirect("integrations:list")
    extra = {k: request.POST.get(k, "") for k, _, _ in cls.extra_fields}
    IntegrationService().save(provider, secret=request.POST.get("secret", ""), extra=extra,
                              enabled=request.POST.get("enabled") == "on", user=request.user, request=request)
    messages.success(request, f"{cls.label} settings saved.")
    return redirect(f"/integrations/#{provider}")


@super_admin_required
@require_POST
def integration_test(request, provider):
    ok, msg = IntegrationService().test(provider)
    (messages.success if ok else messages.error)(request, f"{ADAPTERS[provider].label}: {msg}")
    return redirect(f"/integrations/#{provider}")


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
    choices = [("auto", "Automatic (first one switched on)"), ("offline", OfflineTemplateProvider.label)] + \
              [(name, ADAPTERS[name].label) for name in AI_ORDER]
    ctx = {"choices": choices, "prompt": "", "provider": "auto", "answer": "", "error": "", "used": ""}
    if request.method == "POST":
        prompt = request.POST.get("prompt", "").strip()[:MAX_PROMPT]
        provider = request.POST.get("provider", "auto")
        ctx.update(prompt=prompt, provider=provider)
        ai = service.ai() if provider == "auto" else (OfflineTemplateProvider() if provider == "offline"
                                                        else service.adapter(provider))
        ctx["used"] = ai.label
        if not prompt:
            ctx["error"] = "Please type a prompt."
        else:
            try:
                ctx["answer"] = ai.generate(prompt, max_tokens=300)
            except IntegrationError as exc:
                ctx["error"] = exc.message
    return render(request, "integrations/ai_test.html", ctx)
