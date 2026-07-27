import datetime
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.models import User
from notifications.services import send_email

from .forms import ClaimForm
from .models import Claim, Schedule

CURRENT_SCHEDULE_SESSION_KEY = "current_schedule_id"


def _user_schedules(user):
    if user.is_parent:
        return Schedule.objects.all()
    return Schedule.objects.filter(members=user)


def _resolve_schedule(request, schedule_id=None):
    qs = _user_schedules(request.user)
    schedule = None
    if schedule_id is not None:
        schedule = get_object_or_404(qs, pk=schedule_id)
    else:
        sid = request.session.get(CURRENT_SCHEDULE_SESSION_KEY)
        if sid:
            schedule = qs.filter(pk=sid).first()
        if schedule is None:
            schedule = qs.filter(is_active=True).first() or qs.first()
    if schedule is not None:
        request.session[CURRENT_SCHEDULE_SESSION_KEY] = schedule.id
    return schedule, qs


def _claims_by_day(schedule):
    grouped = defaultdict(list)
    for claim in schedule.claims.select_related("user").all():
        grouped[claim.date].append(claim)
    return grouped


@login_required
def calendar_view(request, schedule_id=None):
    schedule, available = _resolve_schedule(request, schedule_id)
    if schedule is None:
        return render(request, "schedules/calendar.html", {
            "schedule": None, "available_schedules": available,
        })

    grouped = _claims_by_day(schedule)
    days = [
        {"date": day, "claims": grouped.get(day, [])}
        for day in schedule.days
    ]
    my_claims = {c.date for c in schedule.claims.filter(user=request.user)}

    return render(request, "schedules/calendar.html", {
        "schedule": schedule,
        "available_schedules": available,
        "days": days,
        "my_claims": my_claims,
        "claim_form": ClaimForm(),
    })


@login_required
def schedule_list_view(request):
    return render(request, "schedules/schedule_list.html", {
        "schedules": _user_schedules(request.user),
    })


@login_required
@require_POST
def claim_day_view(request, schedule_id, date):
    schedule, _ = _resolve_schedule(request, schedule_id)
    date = datetime.date.fromisoformat(date)

    form = ClaimForm(request.POST)
    if form.is_valid():
        claim, created = Claim.objects.update_or_create(
            schedule=schedule, date=date, user=request.user,
            defaults={"note": form.cleaned_data["note"]},
        )
        if created and schedule.notify_parents_email:
            _notify_parents_of_claim(schedule, claim)
        messages.success(request, "Saved your spot on the calendar.")
    else:
        messages.error(request, "Couldn't save — note was too long.")
    return redirect(reverse("schedules:calendar_for", args=[schedule.id]))


@login_required
@require_POST
def unclaim_day_view(request, schedule_id, date):
    schedule, _ = _resolve_schedule(request, schedule_id)
    date = datetime.date.fromisoformat(date)
    Claim.objects.filter(schedule=schedule, date=date, user=request.user).delete()
    messages.info(request, "Removed your name from that day.")
    return redirect(reverse("schedules:calendar_for", args=[schedule.id]))


@login_required
@require_POST
def remove_claim_view(request, schedule_id, claim_id):
    if not request.user.is_parent:
        raise PermissionDenied("Only parents can remove another person's claim.")
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    Claim.objects.filter(schedule=schedule, pk=claim_id).delete()
    messages.info(request, "Removed that claim.")
    return redirect(reverse("schedules:calendar_for", args=[schedule.id]))


def _notify_parents_of_claim(schedule, claim):
    parent_emails = list(
        User.objects.filter(role=User.Role.PARENT, is_active=True)
        .exclude(email="")
        .values_list("email", flat=True)
    )
    if not parent_emails:
        return
    subject = f"{claim.user.name} claimed {claim.date} on {schedule.name}"
    body = f"{claim.user.name} signed up for {claim.date} on '{schedule.name}'."
    if claim.note:
        body += f"\nNote: {claim.note}"
    send_email(parent_emails, subject, body)
