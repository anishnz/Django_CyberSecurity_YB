"""forms.py - Contact us form, team photo form and meeting photo form. Owner: Dinesh Upreti."""

from django import forms

from .models import ContactMessage, MeetingPhoto


class ContactForm(forms.ModelForm):
    """Contact form with a hidden 'website' field that bots fill in (honeypot spam check)."""

    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "organisation", "topic", "message"]
        widgets = {
            "topic": forms.Select(
                choices=[
                    ("general", "General question"),
                    ("demo", "Ask for a demo"),
                    ("pricing", "Plans and pricing"),
                    ("support", "Help with the app"),
                    ("community", "Community and kura partnership"),
                ]
            ),
            "message": forms.Textarea(attrs={"rows": 5}),
        }

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam check failed.")
        return ""


class TeamMemberForm(forms.Form):
    """Bio and photo for one team member (Website content page)."""

    bio = forms.CharField(
        required=False, max_length=600, widget=forms.Textarea(attrs={"rows": 3}), label="Short bio (own words)"
    )
    photo = forms.ImageField(required=False, label="New photo (JPG, PNG or WebP)")


class MeetingPhotoForm(forms.ModelForm):
    """Upload one real meeting photo for the slider."""

    class Meta:
        model = MeetingPhoto
        fields = ["title", "caption", "place", "taken_on", "image", "order"]
        widgets = {"taken_on": forms.DateInput(attrs={"type": "date"})}
        labels = {"taken_on": "Date taken", "image": "Photo (JPG, PNG or WebP)"}
