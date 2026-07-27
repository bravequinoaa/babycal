from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path("accounts/", include("accounts.urls")),
    path("admin-parents/", include("adminparents.urls")),
    path("help/", include("helppage.urls")),
    path("", include("schedules.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
