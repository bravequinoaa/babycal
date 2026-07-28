from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User

from .models import HelpPage


class MarkdownRenderingTests(TestCase):
    def setUp(self):
        self.fam = User.objects.create_user(phone="+12125550020", name="Fam", role=User.Role.FAM)
        self.client = Client()
        self.client.force_login(self.fam)

    def test_markdown_body_renders_to_html(self):
        help_page = HelpPage.get_solo()
        help_page.body = "**bold text** and a [link](https://example.com)"
        help_page.save()

        response = self.client.get(reverse("helppage:view"))

        self.assertContains(response, "<strong>bold text</strong>")
        self.assertContains(response, '<a href="https://example.com">link</a>')

    def test_disallowed_tags_are_stripped(self):
        help_page = HelpPage.get_solo()
        help_page.body = "<script>alert('xss')</script>safe text"
        help_page.save()

        response = self.client.get(reverse("helppage:view"))

        self.assertNotContains(response, "<script>")
        self.assertContains(response, "safe text")


class HelpEditPreviewTests(TestCase):
    def setUp(self):
        self.parent = User.objects.create_user(
            phone="+12125550021", name="Parent", role=User.Role.PARENT
        )
        self.client = Client()
        self.client.force_login(self.parent)

    def test_edit_page_has_import_and_preview_controls(self):
        response = self.client.get(reverse("helppage:edit"))

        self.assertContains(response, 'id="import-md-btn"')
        self.assertContains(response, 'id="preview-md-btn"')
        self.assertContains(response, 'id="preview-modal"')

    def test_preview_endpoint_renders_markdown(self):
        response = self.client.post(
            reverse("helppage:preview"), {"body": "**bold** text"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("<strong>bold</strong>", response.json()["html"])

    def test_preview_endpoint_requires_parent(self):
        fam = User.objects.create_user(phone="+12125550022", name="Fam", role=User.Role.FAM)
        client = Client()
        client.force_login(fam)

        response = client.post(reverse("helppage:preview"), {"body": "hi"})

        self.assertEqual(response.status_code, 403)
