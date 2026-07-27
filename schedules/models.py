import datetime

from django.conf import settings
from django.db import models


class Baby(models.Model):
    """A non-login profile (Cookie/Snoopy) — display only, per SPEC.md section 2."""

    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to="babies/", blank=True, null=True)
    blurb = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural = "babies"

    def __str__(self):
        return self.name


class Schedule(models.Model):
    name = models.CharField(max_length=150)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    notify_parents_email = models.BooleanField(
        default=False, help_text="Email parents when someone claims a day on this schedule"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="ScheduleMembership", related_name="schedules"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="schedules_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name} ({self.start_date} – {self.end_date})"

    @property
    def days(self):
        span = (self.end_date - self.start_date).days
        return [self.start_date + datetime.timedelta(days=i) for i in range(span + 1)]


class ScheduleMembership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "schedule")

    def __str__(self):
        return f"{self.user} on {self.schedule}"


class Claim(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name="claims")
    date = models.DateField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="claims")
    note = models.CharField(max_length=280, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("schedule", "date", "user")
        ordering = ["date", "created_at"]

    def __str__(self):
        return f"{self.user} on {self.date} ({self.schedule})"
