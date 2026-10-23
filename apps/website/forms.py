"""forms.py - Contact us form. Owner: Dinesh Upreti."""

from django import forms

from .models import ContactMessage


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
