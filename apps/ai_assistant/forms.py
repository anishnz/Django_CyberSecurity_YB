"""forms.py - AI draft request and edit forms. Owner: Dinesh Upreti (screens)."""

from django import forms

from apps.learning.models import LearningTopic

from .models import AIDraft


class DraftRequestForm(forms.Form):
    """What the teacher wants the AI helper to draft."""

    kind = forms.ChoiceField(choices=AIDraft.KINDS, label="What do you need?")
    topic = forms.ModelChoiceField(
        queryset=LearningTopic.objects.select_related("level").order_by("level__number", "sort_order"),
        required=False,
        help_text="Needed if you want to turn a question into a practice question.",
    )
    request_text = forms.CharField(
        max_length=300,
        required=False,
        label="About",
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="For example 'fake prize messages on gaming apps'. Never type student names.",
    )


class DraftEditForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea(attrs={"rows": 10}), max_length=4000)
    needs_cultural_check = forms.BooleanField(
        required=False, label="Has Māori language or tikanga (needs the Cultural Guide)"
    )
