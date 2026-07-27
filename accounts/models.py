import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone, name, password=None, **extra_fields):
        if not phone:
            raise ValueError("Users must have a phone number")
        user = self.model(phone=phone, name=name, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, phone, name="", password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", User.Role.FAM)
        return self._create_user(phone, name, password, **extra_fields)

    def create_superuser(self, phone, name="", password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.PARENT)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(phone, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        PARENT = "parent", "Parent"
        FAM = "fam", "Fam"

    class FamLabel(models.TextChoices):
        UNC = "unc", "Unc"
        ANT = "ant", "Ant"

    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, unique=True, help_text="E.164 format, e.g. +17329861906")
    email = models.EmailField(blank=True, help_text="Only needed for parents to receive claim notifications")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.FAM)
    fam_label = models.CharField(
        max_length=10, choices=FamLabel.choices, blank=True,
        help_text="Cosmetic only (unc/ant) — does not affect permissions",
    )
    partner_name = models.CharField(
        max_length=150, blank=True,
        help_text="Optional second name for couples sharing one Fam account",
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.phone})"

    def save(self, *args, **kwargs):
        if self.phone:
            # Lazy import: services.py imports LoginOTP from this module.
            from .services import normalize_phone

            self.phone = normalize_phone(self.phone)
        super().save(*args, **kwargs)

    @property
    def is_parent(self):
        return self.role == self.Role.PARENT


class LoginOTP(models.Model):
    phone = models.CharField(max_length=20, db_index=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    fallback_used = models.BooleanField(
        default=False, help_text="True when auto-verified because no SMS provider is configured"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"OTP for {self.phone} ({'verified' if self.verified_at else 'pending'})"

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @classmethod
    def issue(cls, phone, ttl_seconds, fallback_used=False):
        code = f"{secrets.randbelow(1_000_000):06d}"
        otp = cls.objects.create(
            phone=phone,
            code=code,
            expires_at=timezone.now() + timedelta(seconds=ttl_seconds),
            fallback_used=fallback_used,
        )
        if fallback_used:
            otp.verified_at = timezone.now()
            otp.save(update_fields=["verified_at"])
        return otp

    def verify(self, code):
        if self.is_expired or self.verified_at:
            return False
        if not secrets.compare_digest(self.code, code):
            return False
        self.verified_at = timezone.now()
        self.save(update_fields=["verified_at"])
        return True


class Invite(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        EXPIRED = "expired", "Expired"

    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    role_label = models.CharField(max_length=10, choices=User.FamLabel.choices, blank=True)
    partner_name = models.CharField(max_length=150, blank=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="invites_sent"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invite({self.name}, {self.phone}, {self.status})"
