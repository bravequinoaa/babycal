from django.urls import path

from . import views

app_name = "schedules"

urlpatterns = [
    path("", views.calendar_view, name="calendar"),
    path("schedules/", views.schedule_list_view, name="schedule_list"),
    path("schedule/<int:schedule_id>/", views.calendar_view, name="calendar_for"),
    path("schedule/<int:schedule_id>/day/<str:date>/claim/", views.claim_day_view, name="claim_day"),
    path("schedule/<int:schedule_id>/day/<str:date>/unclaim/", views.unclaim_day_view, name="unclaim_day"),
    path("schedule/<int:schedule_id>/claim/<int:claim_id>/remove/", views.remove_claim_view, name="remove_claim"),
]
