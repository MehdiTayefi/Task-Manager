from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from tasks.models import Task


User = get_user_model()


class AccountAPITests(APITestCase):
    password = "Violet!River82Cloud"

    def setUp(self):
        self.user = User.objects.create_user(
            username="ali",
            email="ali@example.com",
            password=self.password,
        )

    def login(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.user.username,
                "password": self.password,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        return response.data

    def authenticate(self, access):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )

    def refresh(self, token):
        return self.client.post(
            reverse("accounts:refresh"),
            {"refresh": token},
            format="json",
        )

    def test_register_hashes_password_and_prevents_privilege_escalation(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "sara",
                "email": "sara@example.com",
                "password": self.password,
                "password_confirm": self.password,
                "is_staff": True,
                "is_superuser": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(
            set(response.data),
            {"id", "username", "email"},
        )

        user = User.objects.get(username="sara")

        self.assertNotEqual(user.password, self.password)
        self.assertTrue(user.check_password(self.password))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_register_rejects_invalid_input(self):
        cases = (
            ("username", {"username": "ali"}),
            ("email", {"email": "ali@example.com"}),
            ("password_confirm", {"password_confirm": "different"}),
            (
                "password",
                {"password": "123", "password_confirm": "123"},
            ),
        )

        for field, changes in cases:
            with self.subTest(field=field):
                payload = {
                    "username": "sara",
                    "email": "sara@example.com",
                    "password": self.password,
                    "password_confirm": self.password,
                }
                payload.update(changes)

                response = self.client.post(
                    reverse("accounts:register"),
                    payload,
                    format="json",
                )

                self.assertEqual(response.status_code, 400, response.data)
                self.assertIn(field, response.data)
                self.assertEqual(User.objects.count(), 1)

    def test_login_rejects_wrong_password_and_inactive_user(self):
        url = reverse("accounts:login")

        response = self.client.post(
            url,
            {"username": "ali", "password": "wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        response = self.client.post(
            url,
            {"username": "ali", "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_me_returns_only_current_user_public_fields(self):
        tokens = self.login()
        self.authenticate(tokens["access"])

        response = self.client.get(reverse("users:me"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "id": self.user.pk,
                "username": "ali",
                "email": "ali@example.com",
            },
        )

    def test_me_rejects_missing_invalid_expired_and_refresh_tokens(self):
        expired = AccessToken.for_user(self.user)
        expired.set_exp(lifetime=timedelta(seconds=-1))

        refresh = RefreshToken.for_user(self.user)

        for token in (None, "invalid-token", str(expired), str(refresh)):
            with self.subTest(token=token):
                self.client.credentials()

                if token is not None:
                    self.authenticate(token)

                for method in ("get", "delete"):
                    response = getattr(self.client, method)(
                        reverse("users:me"),
                    )
                    self.assertEqual(response.status_code, 401)

    def test_refresh_rotates_and_rejects_previous_token(self):
        original = self.login()

        response = self.refresh(original["refresh"])

        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertNotEqual(
            response.data["refresh"],
            original["refresh"],
        )

        reused = self.refresh(original["refresh"])
        self.assertEqual(reused.status_code, 401)

        self.authenticate(response.data["access"])
        self.assertEqual(
            self.client.get(reverse("users:me")).status_code,
            200,
        )

        rotated_again = self.refresh(response.data["refresh"])
        self.assertEqual(rotated_again.status_code, 200)

    def test_refresh_rejects_inactive_user(self):
        tokens = self.login()

        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        self.assertEqual(
            self.refresh(tokens["refresh"]).status_code,
            401,
        )

        self.authenticate(tokens["access"])
        self.assertEqual(
            self.client.get(reverse("users:me")).status_code,
            401,
        )

    def test_logout_revokes_only_submitted_refresh(self):
        first = self.login()
        second = self.login()

        response = self.client.post(
            reverse("accounts:logout"),
            {"refresh": first["refresh"]},
            format="json",
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertEqual(
            self.refresh(first["refresh"]).status_code,
            401,
        )
        self.assertEqual(
            self.refresh(second["refresh"]).status_code,
            200,
        )

        self.authenticate(first["access"])
        self.assertEqual(
            self.client.get(reverse("users:me")).status_code,
            200,
        )

    def test_delete_rejects_missing_or_wrong_password(self):
        tokens = self.login()
        self.authenticate(tokens["access"])

        for payload in ({}, {"password": "wrong"}):
            with self.subTest(payload=payload):
                response = self.client.delete(
                    reverse("users:me"),
                    payload,
                    format="json",
                )

                self.assertEqual(response.status_code, 400)
                self.assertTrue(
                    User.objects.filter(pk=self.user.pk).exists(),
                )

        self.assertEqual(
            self.refresh(tokens["refresh"]).status_code,
            200,
        )

    def assert_tokens_revoked(self, pairs):
        for pair in pairs:
            self.authenticate(pair["access"])
            self.assertEqual(
                self.client.get(reverse("users:me")).status_code,
                401,
            )
            self.assertEqual(
                self.refresh(pair["refresh"]).status_code,
                401,
            )

    def test_delete_account_removes_tasks_and_revokes_all_sessions(self):
        pairs = [self.login(), self.login()]
        jtis = [
            RefreshToken(pair["refresh"])["jti"]
            for pair in pairs
        ]
        user_id = self.user.pk

        task = Task.objects.create(owner=self.user, title="Private task")

        other = User.objects.create_user(
            username="sara",
            email="sara@example.com",
            password=self.password,
        )
        other_task = Task.objects.create(owner=other, title="Keep this")

        self.authenticate(pairs[0]["access"])
        response = self.client.delete(
            reverse("users:me"),
            {"password": self.password},
            format="json",
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(User.objects.filter(pk=user_id).exists())
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

        self.assertTrue(User.objects.filter(pk=other.pk).exists())
        self.assertTrue(Task.objects.filter(pk=other_task.pk).exists())

        self.assertEqual(
            BlacklistedToken.objects.filter(token__jti__in=jtis).count(),
            2,
        )
        self.assert_tokens_revoked(pairs)

    def test_admin_single_and_bulk_deletion_revoke_tokens(self):
        admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password=self.password,
        )
        self.client.force_login(admin_user)

        for bulk in (False, True):
            with self.subTest(bulk=bulk):
                self.client.credentials()

                target = User.objects.create_user(
                    username=f"target{bulk}",
                    email=f"target{bulk}@example.com",
                    password=self.password,
                )
                self.user = target

                pairs = [self.login(), self.login()]
                jtis = [
                    RefreshToken(pair["refresh"])["jti"]
                    for pair in pairs
                ]
                user_id = target.pk

                if bulk:
                    response = self.client.post(
                        reverse("admin:accounts_user_changelist"),
                        {
                            "action": "delete_selected",
                            "_selected_action": [str(user_id)],
                            "post": "yes",
                        },
                    )
                else:
                    response = self.client.post(
                        reverse(
                            "admin:accounts_user_delete",
                            args=[user_id],
                        ),
                        {"post": "yes"},
                    )

                self.assertEqual(response.status_code, 302)
                self.assertFalse(
                    User.objects.filter(pk=user_id).exists(),
                )
                self.assertEqual(
                    BlacklistedToken.objects.filter(
                        token__jti__in=jtis,
                    ).count(),
                    2,
                )
                self.assert_tokens_revoked(pairs)
