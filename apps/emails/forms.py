"""forms.py - Email template editor and bulk email form. Owner: Dinesh Upreti (screens)."""
from django import forms

from apps.schools.models import School

from .models import EmailTemplate


class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ["name", "audience", "subject", "body", "is_active"]
        widgets = {"body": forms.Textarea(attrs={"rows": 10})}


class BulkEmailForm(forms.Form):
    template = forms.ModelChoiceField(queryset=EmailTemplate.objects.exclude(audience="system").filter(is_active=True),
                                      help_text="Parents only get emails if their family opted in.")
    school = forms.ModelChoiceField(queryset=School.objects.all(), required=False, empty_label="All schools")
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}), max_length=2000, required=False,
                              help_text="Used for {message} in notice templates.")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None and not user.is_super_admin:
            self.fields.pop("school")
