from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User


class ParentOnlyAccessTests(TestCase):
    def setUp(self):
        self.parent = User.objects.create_user(phone="+15551110010", name="Parent", role=User.Role.PARENT)
        self.fam = User.objects.create_user(phone="+15551110011", name="Fam", role=User.Role.FAM)
        self.client = Client()

    def test_fam_is_denied_dashboard(self):
        self.client.force_login(self.fam)
        response = self.client.get(reverse("adminparents:dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_fam_is_denied_user_list(self):
        self.client.force_login(self.fam)
        response = self.client.get(reverse("adminparents:users"))
        self.assertEqual(response.status_code, 403)

    def test_fam_is_denied_help_edit(self):
        self.client.force_login(self.fam)
        response = self.client.get(reverse("helppage:edit"))
        self.assertEqual(response.status_code, 403)

    def test_parent_can_access_dashboard(self):
        self.client.force_login(self.parent)
        response = self.client.get(reverse("adminparents:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(reverse("adminparents:dashboard"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('adminparents:dashboard')}")
