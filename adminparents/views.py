from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.decorators import parent_required
from accounts.models import Invite, User
from schedules.models import Schedule
from sms.services import send_sms

from .forms import FamMemberForm, InviteForm, ScheduleForm


@parent_required
def dashboard(request):
    return render(request, "adminparents/dashboard.html", {
        "fam_count": User.objects.filter(role=User.Role.FAM).count(),
        "schedule_count": Schedule.objects.count(),
        "pending_invite_count": Invite.objects.filter(status=Invite.Status.PENDING).count(),
    })


@parent_required
def user_list(request):
    return render(request, "adminparents/users.html", {
        "users": User.objects.all(),
        "invites": Invite.objects.filter(status=Invite.Status.PENDING),
    })


@parent_required
def user_add(request):
    form = FamMemberForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Fam member added.")
        return redirect(reverse("adminparents:users"))
    return render(request, "adminparents/user_form.html", {"form": form, "is_new": True})


@parent_required
def user_edit(request, user_id):
    user = get_object_or_404(User, pk=user_id, role=User.Role.FAM)
    form = FamMemberForm(request.POST or None, instance=user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Fam member updated.")
        return redirect(reverse("adminparents:users"))
    return render(request, "adminparents/user_form.html", {"form": form, "is_new": False, "target": user})


@parent_required
@require_POST
def user_toggle_active(request, user_id):
    user = get_object_or_404(User, pk=user_id, role=User.Role.FAM)
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    messages.success(request, f"{user.name} is now {'active' if user.is_active else 'deactivated'}.")
    return redirect(reverse("adminparents:users"))


@parent_required
def invite_create(request):
    form = InviteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        invite = form.save(commit=False)
        invite.created_by = request.user
        invite.save()
        invite_link = request.build_absolute_uri(f"/invite/{invite.token}/")
        send_sms(invite.phone, f"You're invited to BabyCal! Sign up here: {invite_link}")
        messages.success(request, f"Invite created for {invite.name} (stub send logged, not actually sent).")
        return redirect(reverse("adminparents:users"))
    return render(request, "adminparents/invite_form.html", {"form": form})


@parent_required
def schedule_list(request):
    return render(request, "adminparents/schedules.html", {"schedules": Schedule.objects.all()})


@parent_required
def schedule_add(request):
    form = ScheduleForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.instance.created_by = request.user
        schedule = form.save()
        schedule.members.add(request.user)
        messages.success(request, "Schedule created.")
        return redirect(reverse("adminparents:schedules"))
    return render(request, "adminparents/schedule_form.html", {"form": form, "is_new": True})


@parent_required
def schedule_edit(request, schedule_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    form = ScheduleForm(request.POST or None, instance=schedule)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Schedule updated.")
        return redirect(reverse("adminparents:schedules"))
    return render(request, "adminparents/schedule_form.html", {"form": form, "is_new": False, "target": schedule})


@parent_required
@require_POST
def schedule_toggle_active(request, schedule_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    schedule.is_active = not schedule.is_active
    schedule.save(update_fields=["is_active"])
    messages.success(request, f"{schedule.name} is now {'active' if schedule.is_active else 'inactive'}.")
    return redirect(reverse("adminparents:schedules"))
