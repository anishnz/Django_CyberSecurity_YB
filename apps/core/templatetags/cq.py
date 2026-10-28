"""
cq.py - Template tags: {% L 'dashboard' %}, {% safe_url 'name' %}, |simple_format, |nzdate
=========================================================================================

Owner: Dinesh Upreti (tasks D-02, D-03)
"""

from __future__ import annotations

import re

from decimal import Decimal, InvalidOperation

from django import template
from django.urls import NoReverseMatch, reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

from apps.core.labels import label

register = template.Library()


@register.simple_tag
def L(key, english_only=False):  # pylint: disable=invalid-name
    """English (Māori) label."""
    return label(key, english_only)


@register.simple_tag
def safe_url(name, *args):
    """Reverse a URL name; return '' if it does not exist yet (menus stay safe)."""
    try:
        return reverse(name, args=args)
    except NoReverseMatch:
        return ""


@register.filter
def simple_format(text):
    """Escape text, then turn **bold**, '- ' bullets and blank lines into HTML."""
    safe = escape(text or "")
    safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
    out, bullets = [], []
    for line in safe.splitlines():
        if line.strip().startswith("- "):
            bullets.append(f"<li>{line.strip()[2:]}</li>")
            continue
        if bullets:
            out.append("<ul>" + "".join(bullets) + "</ul>")
            bullets = []
        if line.strip():
            out.append(f"<p>{line}</p>")
    if bullets:
        out.append("<ul>" + "".join(bullets) + "</ul>")
    return mark_safe("".join(out))  # nosec - input was escaped first


@register.filter
def nzdate(value, fmt="%d %b %Y"):
    """Date like '06 Oct 2026'."""
    try:
        return value.strftime(fmt)
    except AttributeError:
        return value or ""


@register.filter
def nzd(value):
    """Money like '$12,960.00' (New Zealand dollars, two decimals)."""
    try:
        return f"${Decimal(value):,.2f}"
    except (InvalidOperation, TypeError, ValueError):
        return value


@register.filter
def get_item(mapping, key):
    """dict lookup in templates: {{ mydict|get_item:key }}."""
    try:
        return mapping.get(key)
    except AttributeError:
        return None


@register.filter
def percent_class(value):
    """Colour class for a percentage."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "secondary"
    return "success" if v >= 75 else "warning" if v >= 50 else "danger"


@register.filter
def bs(field):
    """Render a form field with the right Bootstrap class (form-control / form-select)."""
    widget = field.field.widget
    name = type(widget).__name__
    css = "form-select" if "Select" in name else "form-control"
    if field.errors:
        css += " is-invalid"
    return field.as_widget(attrs={"class": css})
