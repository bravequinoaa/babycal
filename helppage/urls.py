from django.urls import path

from . import views

app_name = "helppage"

urlpatterns = [
    path("", views.view_help, name="view"),
    path("edit/", views.edit_help, name="edit"),
]
