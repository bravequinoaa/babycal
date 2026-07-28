from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.decorators import parent_required
from markdownify.templatetags.markdownify import markdownify

from .forms import HelpLinkFormSet, HelpPageForm, HelpPhotoFormSet
from .models import HelpPage


@login_required
def view_help(request):
    help_page = HelpPage.get_solo()
    return render(request, "helppage/view.html", {"help_page": help_page})


@parent_required
def edit_help(request):
    help_page = HelpPage.get_solo()

    if request.method == "POST":
        form = HelpPageForm(request.POST, instance=help_page)
        link_formset = HelpLinkFormSet(request.POST, instance=help_page, prefix="links")
        photo_formset = HelpPhotoFormSet(request.POST, request.FILES, instance=help_page, prefix="photos")
        if form.is_valid() and link_formset.is_valid() and photo_formset.is_valid():
            help_page = form.save(commit=False)
            help_page.updated_by = request.user
            help_page.save()
            link_formset.save()
            photo_formset.save()
            messages.success(request, "Help page updated.")
            return redirect(reverse("helppage:view"))
    else:
        form = HelpPageForm(instance=help_page)
        link_formset = HelpLinkFormSet(instance=help_page, prefix="links")
        photo_formset = HelpPhotoFormSet(instance=help_page, prefix="photos")

    return render(request, "helppage/edit.html", {
        "form": form,
        "link_formset": link_formset,
        "photo_formset": photo_formset,
    })


@parent_required
@require_POST
def preview_help(request):
    html = markdownify(request.POST.get("body", ""))
    return JsonResponse({"html": html})
