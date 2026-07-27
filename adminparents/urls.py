from django.urls import path

from . import views

app_name = "adminparents"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("users/", views.user_list, name="users"),
    path("users/add/", views.user_add, name="user_add"),
    path("users/<int:user_id>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:user_id>/toggle-active/", views.user_toggle_active, name="user_toggle_active"),
    path("invites/add/", views.invite_create, name="invite_add"),
    path("schedules/", views.schedule_list, name="schedules"),
    path("schedules/add/", views.schedule_add, name="schedule_add"),
    path("schedules/<int:schedule_id>/edit/", views.schedule_edit, name="schedule_edit"),
    path("schedules/<int:schedule_id>/toggle-active/", views.schedule_toggle_active, name="schedule_toggle_active"),
]
