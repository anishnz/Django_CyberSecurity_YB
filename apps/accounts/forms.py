"""forms.py - Login, MFA and user management forms. Owner: Anish Shrestha."""

from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model

from apps.schools.models import School

from .roles import ROLE_CHOICES
from .validators import validate_person_name

User = get_user_model()


class LoginForm(forms.Form):
    """Username and password."""

    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "username"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))


class MFACodeForm(forms.Form):
    """6-digit code from the authenticator app, or a backup code."""

    code = forms.CharField(max_length=12, label="Code", widget=forms.TextInput(
        attrs={"autocomplete": "one-time-code", "inputmode": "numeric", "autofocus": True}))


class UserForm(forms.ModelForm):
    """Create or edit a user (Super Admin)."""

    password = forms.CharField(required=False, widget=forms.PasswordInput,
                               help_text="Leave empty to keep the current password.")

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "phone", "role", "school", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["school"].queryset = School.objects.order_by("name")
        self.fields["school"].required = False
        if not self.instance.pk:
            self.fields["password"].required = True
            self.fields["password"].help_text = "At least 8 characters with a letter and a number."

    def clean_first_name(self):
        return validate_person_name(self.cleaned_data["first_name"])

    def clean_last_name(self):
        value = self.cleaned_data.get("last_name", "")
        return validate_person_name(value) if value else value

    def clean(self):
        data = super().clean()
        role, school = data.get("role"), data.get("school")
        if role in ("school_admin", "teacher", "student") and not school:
            self.add_error("school", "This role must belong to a school.")
        return data


class TemporaryUserForm(forms.Form):
    """Make a temporary account for testing or a visitor."""

    role = forms.ChoiceField(choices=[c for c in ROLE_CHOICES if c[0] != "super_admin"])
    school = forms.ModelChoiceField(queryset=School.objects.order_by("name"), required=False)
    minutes = forms.IntegerField(min_value=5, max_value=240, initial=15)


class ResetPasswordForm(forms.Form):
    """Admin sets a new password for a user."""

    new_password = forms.CharField(widget=forms.PasswordInput, help_text="At least 8 characters with a letter and a number.")


class LoginAsForm(forms.Form):
    """Reason for using Login as (saved in the security log)."""

    reason = forms.CharField(max_length=200, min_length=5, widget=forms.TextInput(
        attrs={"placeholder": "e.g. Test ticket TCK-0042 for the teacher"}))
