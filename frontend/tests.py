import json
import re

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

User = get_user_model()


@override_settings(DEBUG=True)
class BrowserAuthenticationTests(TestCase):
    password = "Violet!River82Cloud"

    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password=self.password,
        )
        self.client = Client(enforce_csrf_checks=True)
        page = self.client.get(reverse("frontend:login"))
        self.assertEqual(page.status_code, 200)
        self.csrf = re.search(
            r'<meta name="csrf-token" content="([^"]+)"', page.content.decode(),
        ).group(1)

    def post(self, name, payload=None):
        return self.client.post(
            reverse(f"frontend:{name}"),
            json.dumps(payload or {}), content_type="application/json",
            HTTP_X_CSRFTOKEN=self.csrf,
        )

    def login(self):
        response = self.post("browser-login", {
            "username": "alice", "password": self.password,
        })
        self.assertEqual(response.status_code, 200, response.content)
        return response

    def test_page_routes_and_api_reverse_names_render(self):
        for name in ("register", "login", "account"):
            with self.subTest(name=name):
                response = self.client.get(reverse(f"frontend:{name}"))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'lang="fa"')
                self.assertContains(response, 'class="app-theme"' if name == "account" else 'class="app-theme auth-theme"')
                self.assertContains(response, reverse("users:me"))
                self.assertIn("no-store", response["Cache-Control"])
        self.assertContains(
            self.client.get(reverse("frontend:register")),
            reverse("accounts:register"),
        )

    def test_cookie_auth_endpoints_require_csrf(self):
        for name in ("browser-login", "browser-refresh", "browser-logout"):
            with self.subTest(name=name):
                response = self.client.post(
                    reverse(f"frontend:{name}"), "{}", content_type="application/json",
                )
                self.assertEqual(response.status_code, 403)

    def test_login_keeps_refresh_out_of_json_and_sets_httponly_cookie(self):
        response = self.login()
        self.assertEqual(set(response.json()), {"access"})
        cookie = response.cookies["taskly_refresh"]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Strict")
        self.assertEqual(cookie["path"], "/browser-auth/")
        self.assertFalse(cookie["secure"])
        self.assertIn("no-store", response["Cache-Control"])

        profile = self.client.get(
            reverse("users:me"),
            HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}",
        )
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.json()["username"], "alice")

    @override_settings(DEBUG=False)
    def test_cookie_is_secure_outside_debug_mode(self):
        self.assertTrue(self.login().cookies["taskly_refresh"]["secure"])

    def test_invalid_credentials_and_malformed_input(self):
        response = self.post("browser-login", {
            "username": "alice", "password": "wrong",
        })
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("taskly_refresh", response.cookies)
        response = self.post("browser-login", ["not", "an", "object"])
        self.assertEqual(response.status_code, 400)
        response = self.client.post(
            reverse("frontend:browser-login"), "{", content_type="application/json",
            HTTP_X_CSRFTOKEN=self.csrf,
        )
        self.assertEqual(response.status_code, 400)

    def test_refresh_rotates_cookie_and_old_refresh_is_blacklisted(self):
        login = self.login()
        old = login.cookies["taskly_refresh"].value
        old_jti = RefreshToken(old)["jti"]
        response = self.post("browser-refresh")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), {"access"})
        new = response.cookies["taskly_refresh"].value
        self.assertNotEqual(new, old)
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=old_jti).exists())
        self.assertEqual(self.post("browser-refresh").status_code, 200)
        self.client.cookies["taskly_refresh"] = old
        response = self.post("browser-refresh")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.cookies["taskly_refresh"]["max-age"], 0)

    def test_refresh_requires_cookie_and_rejects_inactive_user(self):
        self.assertEqual(self.post("browser-refresh").status_code, 401)
        self.login()
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        self.assertEqual(self.post("browser-refresh").status_code, 401)

    def test_refresh_rejects_deleted_user(self):
        self.login()
        self.user.delete()
        self.assertEqual(self.post("browser-refresh").status_code, 401)

    def test_logout_blacklists_refresh_and_clears_cookie(self):
        login = self.login()
        jti = RefreshToken(login.cookies["taskly_refresh"].value)["jti"]
        response = self.post("browser-logout")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertEqual(response.cookies["taskly_refresh"]["max-age"], 0)
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=jti).exists())
        self.assertEqual(self.post("browser-refresh").status_code, 401)
        self.assertEqual(self.post("browser-logout").status_code, 204)

    def test_tasks_workspace_is_persian_and_has_real_api_urls(self):
        response = self.client.get(reverse("frontend:tasks"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'lang="fa"')
        self.assertContains(response, 'dir="rtl"')
        self.assertContains(response, 'class="app-theme"')
        self.assertContains(response, reverse("tasks:task-list"))
        self.assertContains(response, reverse("frontend:account"))
        self.assertContains(response, 'id="task-dialog"')
        self.assertContains(response, 'id="menu-toggle"')

    def test_account_uses_charcoal_shell_and_persian_text(self):
        response = self.client.get(reverse("frontend:account"))
        self.assertContains(response, 'class="app-theme"')
        self.assertContains(response, 'lang="fa"')
        self.assertContains(response, 'پروفایل من')
        self.assertContains(response, 'id="delete-account-form"')
        self.assertContains(response, reverse("frontend:tasks"))

    def test_signup_login_and_immediate_task_creation(self):
        registered = self.client.post(
            reverse("accounts:register"),
            json.dumps({"username":"newuser", "email":"new@example.com", "password":self.password, "password_confirm":self.password}),
            content_type="application/json",
        )
        self.assertEqual(registered.status_code, 201, registered.content)
        logged_in = self.post("browser-login", {"username":"newuser", "password":self.password})
        self.assertEqual(logged_in.status_code, 200, logged_in.content)
        response = self.client.post(
            reverse("tasks:task-list"),
            json.dumps({"title":"تمرین جنگو", "priority":"high"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {logged_in.json()['access']}",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["owner"], registered.json()["id"])

    def test_browser_session_can_use_every_task_operation(self):
        token = self.login().json()["access"]
        headers = {"HTTP_AUTHORIZATION":f"Bearer {token}"}
        created = self.client.post(
            reverse("tasks:task-list"), json.dumps({"title":"کار تازه", "priority":"high", "due_date":"2026-12-30"}),
            content_type="application/json", **headers,
        )
        self.assertEqual(created.status_code, 201, created.content)
        detail_url = reverse("tasks:task-detail", args=[created.json()["id"]])
        detail = self.client.get(detail_url, **headers)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["title"], "کار تازه")
        self.assertIn("updated_at", detail.json())
        updated = self.client.patch(detail_url, json.dumps({"status":"done"}), content_type="application/json", **headers)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["status"], "done")
        filtered = self.client.get(reverse("tasks:task-list"), {"status":"done", "priority":"high", "page":1}, **headers)
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(filtered.json()["count"], 1)
        self.assertEqual(self.client.delete(detail_url, **headers).status_code, 204)
        self.assertEqual(self.client.get(detail_url, **headers).status_code, 404)

    def test_browser_account_deletion_checks_password_and_clears_revoked_cookie(self):
        first = self.login()
        second = self.login()
        jtis = [RefreshToken(r.cookies["taskly_refresh"].value)["jti"] for r in (first, second)]
        headers = {"HTTP_AUTHORIZATION":f"Bearer {second.json()['access']}"}
        from tasks.models import Task
        task = Task.objects.create(owner=self.user, title="Private")
        wrong = self.client.delete(reverse("users:me"), json.dumps({"password":"wrong"}), content_type="application/json", **headers)
        self.assertEqual(wrong.status_code, 400)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())
        deleted = self.client.delete(reverse("users:me"), json.dumps({"password":self.password}), content_type="application/json", **headers)
        self.assertEqual(deleted.status_code, 204, deleted.content)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())
        self.assertEqual(BlacklistedToken.objects.filter(token__jti__in=jtis).count(), 2)
        self.assertEqual(self.client.get(reverse("users:me"), **headers).status_code, 401)
        logout = self.post("browser-logout")
        self.assertEqual(logout.status_code, 204)
        self.assertEqual(logout.cookies["taskly_refresh"]["max-age"], 0)
        self.assertEqual(self.post("browser-refresh").status_code, 401)



    def test_auth_pages_use_persian_text_and_local_font(self):
        for name, title in (("login", "ورود به حساب"), ("register", "حساب خودت را بساز")):
            response = self.client.get(reverse(f"frontend:{name}"))
            self.assertContains(response, title)
            self.assertContains(response, 'lang="fa"')
            self.assertContains(response, 'dir="rtl"')
            self.assertContains(response, 'fonts/Vazirmatn.woff2')
            self.assertNotContains(response, 'Show password')
            self.assertNotContains(response, 'Create your account')

    def test_persian_font_is_available_as_static_asset(self):
        from django.contrib.staticfiles import finders
        from pathlib import Path
        path = finders.find("frontend/fonts/Vazirmatn.woff2")
        self.assertIsNotNone(path)
        self.assertEqual(Path(path).read_bytes()[:4], b"wOF2")
        self.assertIsNotNone(finders.find("frontend/fonts/OFL.txt"))
