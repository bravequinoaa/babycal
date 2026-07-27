from django import forms


class ClaimForm(forms.Form):
    note = forms.CharField(max_length=280, required=False, label="Note (optional)")
