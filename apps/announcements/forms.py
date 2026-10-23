"""forms.py - Announcement form. Owner: Dinesh Upreti."""
from django import forms

from .models import Announcement


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ["title", "body", "audience", "school", "starts_on", "ends_on", "is_pinned"]
        widgets = {"body": forms.Textarea(attrs={"rows": 5}), "starts_on": forms.DateInput(attrs={"type": "date"}),
                   "ends_on": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None and not user.is_super_admin:
            self.fields.pop("school")
