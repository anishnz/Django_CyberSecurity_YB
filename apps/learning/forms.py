"""forms.py - Question form for teachers and the Super Admin. Owner: Anish Shrestha (task A-12)."""
from __future__ import annotations

from django import forms

from .categories import CATEGORIES, LEVEL_CATEGORIES
from .models import Q_TYPES, Level


class QuestionForm(forms.Form):
    """One form for every question type; QuestionFactory checks the rules."""

    level = forms.ModelChoiceField(queryset=Level.objects.all(), to_field_name="number")
    category = forms.ChoiceField(choices=[(c, n) for c, (n, _) in CATEGORIES.items()])
    q_type = forms.ChoiceField(choices=Q_TYPES, label="Question type")
    scenario_text = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}),
                                    label="Scenario story (scenario questions only)")
    text = forms.CharField(max_length=400, widget=forms.Textarea(attrs={"rows": 2}), label="Question")
    option_a = forms.CharField(max_length=300, required=False, label="Option A")
    option_b = forms.CharField(max_length=300, required=False, label="Option B")
    option_c = forms.CharField(max_length=300, required=False, label="Option C")
    option_d = forms.CharField(max_length=300, required=False, label="Option D")
    correct = forms.MultipleChoiceField(choices=[(x, x) for x in "ABCD"], widget=forms.CheckboxSelectMultiple,
                                        label="Correct answer(s)")
    feedback = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), label="Feedback (why the answer is safe)")

    def clean(self):
        data = super().clean()
        level, category = data.get("level"), data.get("category")
        if level and category and category not in LEVEL_CATEGORIES.get(level.number, []):
            self.add_error("category", f"Level {level.number} uses only: {', '.join(LEVEL_CATEGORIES[level.number])}.")
        if data.get("q_type") == "true_false":
            data["option_a"], data["option_b"], data["option_c"], data["option_d"] = "True", "False", "", ""
        elif not data.get("option_a") or not data.get("option_b"):
            self.add_error("option_a", "Options A and B are needed.")
        return data

    def as_factory_data(self) -> dict:
        d = self.cleaned_data
        options = {k.upper(): d[f"option_{k}"] for k in "abcd" if d.get(f"option_{k}")}
        return {"level": d["level"].number, "category": d["category"], "text": d["text"], "options": options,
                "answer": d["correct"], "feedback": d["feedback"], "scenario_text": d.get("scenario_text", "")}
