"""forms.py - Payment (payslip upload) form. Owner: Dinesh Upreti."""
from django import forms

from apps.licensing.plans import LEVEL_PACK_PRICES

from .services import MONTH_CHOICES, PAID_PLANS


class PaymentForm(forms.Form):
    purpose = forms.ChoiceField(choices=[("plan", "Licence plan"), ("pack", "Level Pack")], widget=forms.RadioSelect,
                                initial="plan", label="What are you paying for?")
    plan = forms.ChoiceField(choices=[(p, p.title()) for p in PAID_PLANS], required=False)
    months = forms.TypedChoiceField(choices=[(m, f"{m} month{'s' if m > 1 else ''}") for m in MONTH_CHOICES],
                                    coerce=int, required=False, initial=12)
    level = forms.TypedChoiceField(choices=[(lv, f"Level {lv}") for lv in LEVEL_PACK_PRICES], coerce=int, required=False,
                                   label="Level Pack")
    bank_reference = forms.CharField(max_length=40, help_text="What you typed as the reference at the bank.")
    paid_on = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="Date you paid")
    payslip = forms.FileField(label="Payslip or bank receipt",
                              help_text="PDF, JPG or PNG, up to the document size limit. Please hide other account numbers.")
