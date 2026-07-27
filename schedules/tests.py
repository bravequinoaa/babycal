import datetime

from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User

from .models import Claim, Schedule


class ClaimUniquenessTests(TestCase):
    def setUp(self):
        self.schedule = Schedule.objects.create(
            name="August trip", start_date=datetime.date(2026, 8, 1), end_date=datetime.date(2026, 8, 5)
        )
        self.aunt = User.objects.create_user(phone="+15551110001", name="Aunt Sue", role=User.Role.FAM)
        self.uncle = User.objects.create_user(phone="+15551110002", name="Uncle Bob", role=User.Role.FAM)

    def test_same_user_cannot_double_claim_a_day(self):
        Claim.objects.create(schedule=self.schedule, date=datetime.date(2026, 8, 1), user=self.aunt)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Claim.objects.create(schedule=self.schedule, date=datetime.date(2026, 8, 1), user=self.aunt)

    def test_unlimited_distinct_users_per_day(self):
        Claim.objects.create(schedule=self.schedule, date=datetime.date(2026, 8, 1), user=self.aunt)
        Claim.objects.create(schedule=self.schedule, date=datetime.date(2026, 8, 1), user=self.uncle)
        self.assertEqual(
            Claim.objects.filter(schedule=self.schedule, date=datetime.date(2026, 8, 1)).count(), 2
        )


class CalendarAccessTests(TestCase):
    def setUp(self):
        self.schedule = Schedule.objects.create(
            name="August trip", start_date=datetime.date(2026, 8, 1), end_date=datetime.date(2026, 8, 3)
        )
        self.member = User.objects.create_user(phone="+15551110003", name="Member", role=User.Role.FAM)
        self.non_member = User.objects.create_user(phone="+15551110004", name="Outsider", role=User.Role.FAM)
        self.parent = User.objects.create_user(phone="+15551110005", name="Parent", role=User.Role.PARENT)
        self.schedule.members.add(self.member)
        self.client = Client()

    def test_non_member_cannot_view_schedule(self):
        self.client.force_login(self.non_member)
        response = self.client.get(reverse("schedules:calendar_for", args=[self.schedule.id]))
        self.assertEqual(response.status_code, 404)

    def test_member_can_claim_a_day(self):
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("schedules:claim_day", args=[self.schedule.id, "2026-08-01"]),
            {"note": "Bringing extra treats"},
        )
        self.assertRedirects(response, reverse("schedules:calendar_for", args=[self.schedule.id]))
        claim = Claim.objects.get(schedule=self.schedule, date=datetime.date(2026, 8, 1), user=self.member)
        self.assertEqual(claim.note, "Bringing extra treats")

    def test_fam_cannot_remove_another_users_claim(self):
        claim = Claim.objects.create(schedule=self.schedule, date=datetime.date(2026, 8, 1), user=self.member)
        other_fam = User.objects.create_user(phone="+15551110006", name="Other Fam", role=User.Role.FAM)
        self.schedule.members.add(other_fam)
        self.client.force_login(other_fam)
        response = self.client.post(reverse("schedules:remove_claim", args=[self.schedule.id, claim.id]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Claim.objects.filter(pk=claim.id).exists())

    def test_parent_can_remove_any_claim(self):
        claim = Claim.objects.create(schedule=self.schedule, date=datetime.date(2026, 8, 1), user=self.member)
        self.client.force_login(self.parent)
        response = self.client.post(reverse("schedules:remove_claim", args=[self.schedule.id, claim.id]))
        self.assertRedirects(response, reverse("schedules:calendar_for", args=[self.schedule.id]))
        self.assertFalse(Claim.objects.filter(pk=claim.id).exists())
