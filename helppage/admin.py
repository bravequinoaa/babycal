from django.contrib import admin

from .models import HelpLink, HelpPage, HelpPhoto


class HelpLinkInline(admin.TabularInline):
    model = HelpLink
    extra = 1


class HelpPhotoInline(admin.TabularInline):
    model = HelpPhoto
    extra = 1


@admin.register(HelpPage)
class HelpPageAdmin(admin.ModelAdmin):
    list_display = ["title", "updated_at", "updated_by"]
    inlines = [HelpLinkInline, HelpPhotoInline]
