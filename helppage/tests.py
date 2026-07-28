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
