from django import forms
from django.forms import inlineformset_factory

from .models import HelpLink, HelpPage, HelpPhoto


class HelpPageForm(forms.ModelForm):
    class Meta:
        model = HelpPage
        fields = ["title", "body", "contact_info"]


HelpLinkFormSet = inlineformset_factory(
    HelpPage, HelpLink, fields=["label", "url", "order"], extra=1, can_delete=True
)

HelpPhotoFormSet = inlineformset_factory(
    HelpPage, HelpPhoto, fields=["image", "caption", "order"], extra=1, can_delete=True
)
