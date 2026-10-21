import io
import json
import re
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from tasks.models import Task
from .models import DemoSession
from .api.services import cleanup_expired, create_demo

User = get_user_model()


@override_settings(DEBUG=True, DEMO_CREATE_RATE="1000/hour", DEMO_SESSION_MINUTES=30)
class IsolatedDemoTests(TestCase):
    def setUp(self):
        cache.clear()

    def browser(self):
        client = Client(enforce_csrf_checks=True)
        page = client.get(reverse("frontend:login"))
        token = re.search(r'<meta name="csrf-token" content="([^"]+)"', page.content.decode()).group(1)
        return client, token

    def start(self, client=None, csrf=None):
        if client is None:
            client, csrf = self.browser()
        response = client.post(reverse("demo:start"), "{}", content_type="application/json", HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(response.status_code, 201, response.content)
        return client, csrf, response

    def owner(self, response):
        return AccessToken(response.json()["access"])[api_settings.USER_ID_CLAIM]

    def headers(self, response):
        return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['access']}"}

    def test_start_has_private_data_real_tokens_and_httponly_cookie(self):
        client, csrf, response = self.start()
        user = User.objects.get(pk=self.owner(response))
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertNotIn("refresh", response.json())
        self.assertTrue(response.cookies["taskly_refresh"]["httponly"])
        self.assertLessEqual(int(response.cookies["taskly_refresh"]["max-age"]), 1800)
        self.assertEqual(Task.objects.filter(owner=user).count(), 13)
        self.assertEqual(set(user.tasks.values_list("status", flat=True)), {"todo", "in_progress", "done"})
        listing = client.get(reverse("tasks:task-list"), **self.headers(response))
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.json()["count"], 13)
        self.assertEqual(len(listing.json()["results"]), 10)
        self.assertEqual(listing.json()["results"][0]["title"],"تکمیل گزارش پروژه",)

    def test_two_visitors_never_share_tasks_or_mutate_each_other(self):
        a, _, first = self.start()
        b, _, second = self.start()
        first_id, second_id = self.owner(first), self.owner(second)
        self.assertNotEqual(first_id, second_id)
        self.assertEqual(DemoSession.objects.count(), 2)
        task = Task.objects.filter(owner_id=first_id).first()
        url = reverse("tasks:task-detail", args=[task.pk])
        for method in ("get", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(b, method)(url, json.dumps({"title":"Changed"}) if method != "get" else None, content_type="application/json", **self.headers(second))
                self.assertEqual(response.status_code, 404)
        edited = a.patch(url, json.dumps({"title":"فقط برای نفر اول"}), content_type="application/json", **self.headers(first))
        self.assertEqual(edited.status_code, 200)
        self.assertFalse(Task.objects.filter(owner_id=second_id, title="فقط برای نفر اول").exists())
        self.assertEqual(Task.objects.filter(owner_id=second_id).count(), 13)

    def test_demo_button_does_not_need_signup_but_requires_csrf(self):
        client, _ = self.browser()
        response = client.post(reverse("demo:start"), "{}", content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(DemoSession.objects.count(), 0)
        self.assertEqual(client.get(reverse("demo:start")).status_code, 405)

    def test_rotation_does_not_extend_fixed_deadline_and_reuse_fails(self):
        client, csrf, first = self.start()
        deadline = timezone.now() + timedelta(seconds=90)
        DemoSession.objects.filter(user_id=self.owner(first)).update(expires_at=deadline)
        previous = first.cookies["taskly_refresh"].value
        for _ in range(2):
            rotated = client.post(reverse("frontend:browser-refresh"), "{}", content_type="application/json", HTTP_X_CSRFTOKEN=csrf)
            self.assertEqual(rotated.status_code, 200, rotated.content)
            access = AccessToken(rotated.json()["access"])
            refresh = RefreshToken(rotated.cookies["taskly_refresh"].value)
            self.assertLessEqual(access["exp"], int(deadline.timestamp()))
            self.assertLessEqual(refresh["exp"], int(deadline.timestamp()))
        raw = client.post(reverse("accounts:refresh"), json.dumps({"refresh":previous}), content_type="application/json")
        self.assertEqual(raw.status_code, 401)

    def test_raw_refresh_endpoint_is_also_bounded_by_guest_expiry(self):
        client, _, first = self.start()
        session = DemoSession.objects.get(user_id=self.owner(first))
        raw = client.post(reverse("accounts:refresh"), json.dumps({"refresh":first.cookies["taskly_refresh"].value}), content_type="application/json")
        self.assertEqual(raw.status_code, 200, raw.content)
        self.assertLessEqual(RefreshToken(raw.json()["refresh"])["exp"], int(session.expires_at.timestamp()))
        self.assertLessEqual(AccessToken(raw.json()["access"])["exp"], int(session.expires_at.timestamp()))

    def test_expired_guest_is_deleted_before_api_access(self):
        client, _, first = self.start()
        user_id = self.owner(first)
        DemoSession.objects.filter(user_id=user_id).update(expires_at=timezone.now()-timedelta(seconds=1))
        response = client.get(reverse("tasks:task-list"), **self.headers(first))
        self.assertEqual(response.status_code, 401)
        self.assertFalse(User.objects.filter(pk=user_id).exists())
        self.assertFalse(Task.objects.filter(owner_id=user_id).exists())
        self.assertFalse(DemoSession.objects.filter(user_id=user_id).exists())

    def test_logout_deletes_only_this_guest_and_all_its_tasks(self):
        a, csrf, first = self.start()
        _, _, second = self.start()
        jti = RefreshToken(first.cookies["taskly_refresh"].value)["jti"]
        response = a.post(reverse("frontend:browser-logout"), "{}", content_type="application/json", HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(User.objects.filter(pk=self.owner(first)).exists())
        self.assertFalse(Task.objects.filter(owner_id=self.owner(first)).exists())
        self.assertTrue(User.objects.filter(pk=self.owner(second)).exists())
        self.assertEqual(Task.objects.filter(owner_id=self.owner(second)).count(), 13)
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=jti).exists())

    def test_starting_again_gets_fresh_samples_and_retires_old_guest(self):
        client, csrf, first = self.start()
        Task.objects.filter(owner_id=self.owner(first)).delete()
        _, _, second = self.start(client, csrf)
        self.assertNotEqual(self.owner(first), self.owner(second))
        self.assertFalse(User.objects.filter(pk=self.owner(first)).exists())
        self.assertEqual(Task.objects.filter(owner_id=self.owner(second)).count(), 13)

    def test_cleanup_worker_preserves_normal_accounts_and_active_guests(self):
        normal = User.objects.create_user(username="demo_regular", email="normal@example.com", password="Strong!Example334")
        normal_task = Task.objects.create(owner=normal, title="Keep")
        old, _ = create_demo()
        active, _ = create_demo()
        old_id = old.user_id
        DemoSession.objects.filter(pk=old.pk).update(expires_at=timezone.now()-timedelta(minutes=1))
        call_command("cleanup_demo", stdout=io.StringIO())
        self.assertFalse(User.objects.filter(pk=old_id).exists())
        self.assertTrue(User.objects.filter(pk=active.user_id).exists())
        self.assertTrue(User.objects.filter(pk=normal.pk).exists())
        self.assertTrue(Task.objects.filter(pk=normal_task.pk).exists())
        self.assertEqual(cleanup_expired(), 0)

    def test_looping_worker_cleans_without_http_traffic(self):
        old, _ = create_demo()
        DemoSession.objects.filter(pk=old.pk).update(expires_at=timezone.now()-timedelta(minutes=1))
        with patch("demo.management.commands.cleanup_demo.time.sleep", side_effect=KeyboardInterrupt):
            call_command("cleanup_demo", loop=True, interval=60, stdout=io.StringIO())
        self.assertFalse(User.objects.filter(pk=old.user_id).exists())

    def test_failed_seed_rolls_back_guest_and_session(self):
        with patch("demo.api.services.Task.objects.create", side_effect=RuntimeError("seed failure")):
            with self.assertRaises(RuntimeError):
                create_demo()
        self.assertEqual(DemoSession.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Task.objects.count(), 0)

    @override_settings(DEMO_CREATE_RATE="1/hour")
    def test_demo_creation_is_rate_limited(self):
        client, csrf, _ = self.start()
        response = client.post(reverse("demo:start"), "{}", content_type="application/json", HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response)
        self.assertEqual(DemoSession.objects.count(), 1)

    def test_normal_login_and_demo_status_do_not_change_normal_account(self):
        normal = User.objects.create_user(username="ordinary", email="ordinary@example.com", password="Strong!Example334")
        task = Task.objects.create(owner=normal, title="Real task")
        client, csrf = self.browser()
        response = client.post(reverse("frontend:browser-login"), json.dumps({"username":"ordinary", "password":"Strong!Example334"}), content_type="application/json", HTTP_X_CSRFTOKEN=csrf)
        status = client.get(reverse("demo:status"), **self.headers(response))
        self.assertEqual(status.status_code, 200)
        self.assertFalse(status.json()["is_demo"])
        self.start(client, csrf)
        self.assertTrue(User.objects.filter(pk=normal.pk).exists())
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())

    def test_guest_status_and_ui_entry_points(self):
        client, _, response = self.start()
        status = client.get(reverse("demo:status"), **self.headers(response))
        self.assertEqual(status.status_code, 200)
        self.assertTrue(status.json()["is_demo"])
        self.assertIn("expires_at", status.json())
        for page in ("login", "register"):
            html = client.get(reverse(f"frontend:{page}"))
            self.assertContains(html, "امتحان دمو")
            self.assertContains(html, reverse("demo:start"))
