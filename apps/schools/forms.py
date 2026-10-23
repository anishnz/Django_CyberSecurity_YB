"""forms.py - School, class, section, student and teacher forms. Owner: Rajneesh Kumar."""
from __future__ import annotations

from django import forms

from .models import School, Section


class SchoolForm(forms.ModelForm):
    """Create a school (Super Admin)."""

    class Meta:
        model = School
        fields = ["code", "name", "region", "address", "contact_email", "latitude", "longitude", "logo"]
        help_texts = {"latitude": "Optional – used for the Google Map.", "longitude": "Optional."}

    def clean_code(self):
        return School.clean_code(self.cleaned_data["code"])


class ClassForm(forms.Form):
    name = forms.CharField(max_length=60, label="Class name", help_text="e.g. Year 7")
    year_level = forms.IntegerField(min_value=1, max_value=15)


class SectionForm(forms.Form):
    name = forms.CharField(max_length=40, label="Section name", help_text="e.g. 7A")


class StudentForm(forms.Form):
    """Add a student (School Admin)."""

    first_name = forms.CharField(max_length=60)
    last_name = forms.CharField(max_length=60)
    section = forms.ModelChoiceField(queryset=Section.objects.none())
    password = forms.CharField(widget=forms.PasswordInput, help_text="At least 8 characters with a letter and a number.")
    family_consent = forms.BooleanField(required=False, label="Family (whānau) consent form received")
    parent_name = forms.CharField(max_length=120, required=False)
    parent_email = forms.EmailField(required=False)
    parent_opt_in = forms.BooleanField(required=False, label="Parent agreed to emails and messages")

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["section"].queryset = Section.objects.filter(school_class__school=school).select_related("school_class")


class StudentEditForm(forms.Form):
    """Edit a student's section, consent and parent details."""

    section = forms.ModelChoiceField(queryset=Section.objects.none())
    family_consent = forms.BooleanField(required=False, label="Family (whānau) consent form received")
    parent_name = forms.CharField(max_length=120, required=False)
    parent_email = forms.EmailField(required=False)
    parent_phone = forms.CharField(max_length=30, required=False)
    parent_opt_in = forms.BooleanField(required=False, label="Parent agreed to emails and messages")

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["section"].queryset = Section.objects.filter(school_class__school=school).select_related("school_class")


class TeacherForm(forms.Form):
    first_name = forms.CharField(max_length=60)
    last_name = forms.CharField(max_length=60)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput, help_text="At least 8 characters with a letter and a number.")


class CsvImportForm(forms.Form):
    file = forms.FileField(label="Students CSV file", help_text="Maximum 2 MB. Use the template below.")

    def clean_file(self):
        f = self.cleaned_data["file"]
        if f.size > 2 * 1024 * 1024:
            raise forms.ValidationError("The CSV file is bigger than 2 MB.")
        if not f.name.lower().endswith(".csv"):
            raise forms.ValidationError("Please upload a .csv file.")
        return f
