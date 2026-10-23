"""forms.py - Ticket forms. Owner: Dinesh Upreti (task D-14)."""

from django import forms

from .models import Ticket


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultiFileField(forms.FileField):
    """Up to 3 files; each one is checked later by check_upload (type + size)."""

    widget = MultiFileInput

    def clean(self, data, initial=None):
        files = data if isinstance(data, (list, tuple)) else ([data] if data else [])
        if len(files) > 3:
            raise forms.ValidationError("You can attach up to 3 files.")
        return [super().clean(f, initial) for f in files]


ATTACH_HELP = "Optional. Up to 3 screenshots or PDFs (JPG, PNG, PDF). Please hide passwords and personal details."


class TicketForm(forms.ModelForm):
    """New ticket: title, category, priority, description and up to 3 files."""

    files = MultiFileField(required=False, label="Screenshots or files", help_text=ATTACH_HELP)

    class Meta:
        model = Ticket
        fields = ["title", "category", "priority", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 6, "maxlength": 5000})}
        help_texts = {"title": "A few words, for example 'Cannot open Level 3'."}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].choices = [c for c in Ticket.CATEGORIES if c[0] != "contact"]
        if user is not None and user.is_student:
            self.fields["priority"].choices = [("normal", "Normal"), ("low", "Low")]


class CommentForm(forms.Form):
    body = forms.CharField(label="Your reply", widget=forms.Textarea(attrs={"rows": 4}), max_length=5000)
    files = MultiFileField(required=False, label="Screenshots or files", help_text=ATTACH_HELP)
    internal = forms.BooleanField(required=False, label="Internal note (only staff can see it)")


class ReportQuestionForm(forms.Form):
    note = forms.CharField(
        label="What looks wrong?",
        widget=forms.Textarea(attrs={"rows": 4}),
        max_length=1000,
        help_text="For example: 'Two answers look right' or 'There is a spelling mistake'.",
    )
