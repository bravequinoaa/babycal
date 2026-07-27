from django.conf import settings
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field


class HelpPage(models.Model):
    """Singleton — always fetched/edited via HelpPage.get_solo()."""

    title = models.CharField(max_length=150, default="Help")
    body = CKEditor5Field(blank=True, config_name="default")
    contact_info = models.CharField(max_length=255, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class HelpLink(models.Model):
    help_page = models.ForeignKey(HelpPage, on_delete=models.CASCADE, related_name="links")
    label = models.CharField(max_length=100)
    url = models.URLField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.label


class HelpPhoto(models.Model):
    help_page = models.ForeignKey(HelpPage, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="help_photos/")
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.caption or f"Photo {self.pk}"
