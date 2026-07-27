from django import forms

from .services import InvalidPhoneNumber, normalize_phone


class PhoneLoginForm(forms.Form):
    phone = forms.CharField(label="Phone number", max_length=30)

    def clean_phone(self):
        raw = self.cleaned_data["phone"]
        try:
            return normalize_phone(raw)
        except InvalidPhoneNumber as exc:
            raise forms.ValidationError("Enter a valid US phone number.") from exc


class OTPVerifyForm(forms.Form):
    code = forms.CharField(label="Verification code", max_length=6)
