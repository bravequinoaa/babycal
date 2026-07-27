from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Invite, LoginOTP, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    ordering = ["name"]
    list_display = ["name", "phone", "role", "fam_label", "is_active", "is_staff"]
    list_filter = ["role", "fam_label", "is_active"]
    search_fields = ["name", "phone", "email"]
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Profile", {"fields": ("name", "email", "role", "fam_label", "partner_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone", "name", "role", "password1", "password2"),
        }),
    )


@admin.register(LoginOTP)
class LoginOTPAdmin(admin.ModelAdmin):
    list_display = ["phone", "created_at", "expires_at", "verified_at", "fallback_used"]
    list_filter = ["fallback_used"]
    readonly_fields = [f.name for f in LoginOTP._meta.fields]


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "status", "created_at", "sent_at"]
    list_filter = ["status"]
