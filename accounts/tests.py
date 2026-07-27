from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import LoginOTP, User
from .services import InvalidPhoneNumber, normalize_phone


class NormalizePhoneTests(TestCase):
    def test_accepts_messy_input(self):
        self.assertEqual(normalize_phone("(732) 986-1906"), "+17329861906")
        self.assertEqual(normalize_phone("973-489-1380"), "+19734891380")
        self.assertEqual(normalize_phone("+17329861906"), "+17329861906")

    def test_rejects_invalid_number(self):
        with self.assertRaises(InvalidPhoneNumber):
            normalize_phone("123")


@override_settings(OTP_PROVIDER_ENABLED=False)
class LoginFallbackTests(TestCase):
    """No SMS provider configured -> login skips verification (SPEC.md section 3)."""

    def setUp(self):
        self.user = User.objects.create_user(phone="+17329861906", name="Wil", role=User.Role.PARENT)
        self.client = Client()

    def test_known_phone_logs_in_without_otp_step(self):
        response = self.client.post(reverse("accounts:login"), {"phone": "(732) 986-1906"}, follow=True)
        self.assertEqual(response.wsgi_request.user, self.user)
        otp = LoginOTP.objects.get(phone="+17329861906")
        self.assertTrue(otp.fallback_used)
        self.assertIsNotNone(otp.verified_at)

    def test_unknown_phone_is_rejected(self):
        response = self.client.post(reverse("accounts:login"), {"phone": "+12125551234"})
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, "hasn&#x27;t been invited")

    def test_inactive_user_cannot_log_in(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(reverse("accounts:login"), {"phone": "+17329861906"})
        self.assertFalse(response.wsgi_request.user.is_authenticated)


@override_settings(OTP_PROVIDER_ENABLED=True)
class LoginWithOtpTests(TestCase):
    """SMS provider configured -> real code entry is required."""

    def setUp(self):
        self.user = User.objects.create_user(phone="+17329861906", name="Wil", role=User.Role.PARENT)
        self.client = Client()

    def test_requires_verify_step(self):
        response = self.client.post(reverse("accounts:login"), {"phone": "+17329861906"})
        self.assertRedirects(response, reverse("accounts:verify"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_correct_code_logs_in(self):
        self.client.post(reverse("accounts:login"), {"phone": "+17329861906"})
        otp = LoginOTP.objects.get(phone="+17329861906")
        response = self.client.post(reverse("accounts:verify"), {"code": otp.code}, follow=True)
        self.assertEqual(response.wsgi_request.user, self.user)

    def test_wrong_code_is_rejected(self):
        self.client.post(reverse("accounts:login"), {"phone": "+17329861906"})
        response = self.client.post(reverse("accounts:verify"), {"code": "000000"})
        self.assertFalse(response.wsgi_request.user.is_authenticated)
