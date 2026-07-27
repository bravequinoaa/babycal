from django.contrib import admin

from .models import Baby, Claim, Schedule, ScheduleMembership


class ScheduleMembershipInline(admin.TabularInline):
    model = ScheduleMembership
    extra = 1


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ["name", "start_date", "end_date", "is_active", "notify_parents_email"]
    list_filter = ["is_active"]
    inlines = [ScheduleMembershipInline]


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ["schedule", "date", "user", "note", "created_at"]
    list_filter = ["schedule"]
    search_fields = ["user__name", "note"]


@admin.register(Baby)
class BabyAdmin(admin.ModelAdmin):
    list_display = ["name"]
