from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import OTPVerifyForm, PhoneLoginForm
from .models import LoginOTP, User
from .services import start_login

SESSION_PENDING_PHONE = "pending_login_phone"


def _log_user_in(request, phone):
    user = authenticate(request, phone=phone)
    if user is None:
        return False
    login(request, user)
    return True


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect(reverse("schedules:calendar"))

    form = PhoneLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        phone = form.cleaned_data["phone"]
        if not User.objects.filter(phone=phone, is_active=True).exists():
            form.add_error("phone", "That number hasn't been invited yet.")
        else:
            otp = start_login(phone)
            if otp.fallback_used:
                _log_user_in(request, phone)
                return redirect(reverse("schedules:calendar"))
            request.session[SESSION_PENDING_PHONE] = phone
            return redirect(reverse("accounts:verify"))

    return render(request, "accounts/login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def verify_view(request):
    phone = request.session.get(SESSION_PENDING_PHONE)
    if not phone:
        return redirect(reverse("accounts:login"))

    form = OTPVerifyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        otp = (
            LoginOTP.objects.filter(phone=phone, verified_at__isnull=True)
            .order_by("-created_at")
            .first()
        )
        if otp and otp.verify(form.cleaned_data["code"]):
            del request.session[SESSION_PENDING_PHONE]
            _log_user_in(request, phone)
            return redirect(reverse("schedules:calendar"))
        form.add_error("code", "That code is incorrect or expired.")

    return render(request, "accounts/verify.html", {"form": form, "phone": phone})


@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    return redirect(reverse("accounts:login"))
