from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import ContactInquiry


_INPUT_CLASSES: str = (
    "w-full p-3 border border-gray-300 rounded-lg "
    "bg-white text-gray-900 "
    "dark:bg-gray-800 dark:text-gray-100 dark:border-gray-700 "
    "focus:outline-none focus:ring-2 focus:ring-green-500 "
    "transition"
)
_TEXTAREA_CLASSES: str = _INPUT_CLASSES + " min-h-[140px] resize-y"


class ContactInquiryForm(forms.ModelForm):
    """Form for submitting a contact inquiry from the public site."""

    class Meta:
        model = ContactInquiry
        fields = ("name", "email", "subject", "message")
        labels = {
            "name": _("Your Name"),
            "email": _("Your Email"),
            "subject": _("Subject"),
            "message": _("Project Details / Message"),
        }
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": _INPUT_CLASSES,
                    "placeholder": _("Jane Doe"),
                    "autocomplete": "name",
                    "required": True,
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": _INPUT_CLASSES,
                    "placeholder": _("you@example.com"),
                    "autocomplete": "email",
                    "required": True,
                }
            ),
            "subject": forms.TextInput(
                attrs={
                    "class": _INPUT_CLASSES,
                    "placeholder": _("Brief subject"),
                    "maxlength": 200,
                    "required": True,
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "class": _TEXTAREA_CLASSES,
                    "placeholder": _(
                        "Tell me about your project, timeline, and budget..."
                    ),
                    "rows": 6,
                    "required": True,
                }
            ),
        }

    def clean_message(self) -> str:
        message: str = (self.cleaned_data.get("message") or "").strip()
        if len(message) < 10:
            raise forms.ValidationError(
                _("Please provide at least 10 characters of detail.")
            )
        return message