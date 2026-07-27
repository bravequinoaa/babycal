from django import forms

from accounts.models import Invite, User
from accounts.services import InvalidPhoneNumber, normalize_phone
from schedules.models import Schedule


class _NormalizesPhoneMixin:
    def clean_phone(self):
        raw = self.cleaned_data["phone"]
        try:
            return normalize_phone(raw)
        except InvalidPhoneNumber as exc:
            raise forms.ValidationError("Enter a valid US phone number.") from exc


class FamMemberForm(_NormalizesPhoneMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "phone", "email", "fam_label", "partner_name", "is_active"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.FAM
        if commit:
            user.save()
        return user


class InviteForm(_NormalizesPhoneMixin, forms.ModelForm):
    class Meta:
        model = Invite
        fields = ["name", "phone", "role_label", "partner_name"]


class ScheduleForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Schedule
        fields = ["name", "start_date", "end_date", "is_active", "notify_parents_email"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["members"].initial = self.instance.members.all()

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start_date"), cleaned.get("end_date")
        if start and end and end < start:
            raise forms.ValidationError("End date must be on or after the start date.")
        return cleaned

    def save(self, commit=True):
        schedule = super().save(commit=commit)
        if commit:
            schedule.members.set(self.cleaned_data["members"])
        return schedule
