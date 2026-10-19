from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APITestCase

from .models import Task


User = get_user_model()


class TaskAPITests(APITestCase):
    password = "Violet!River82Cloud"

    def setUp(self):
        self.user = User.objects.create_user(
            username="ali",
            email="ali@example.com",
            password=self.password,
        )
        self.other = User.objects.create_user(
            username="sara",
            email="sara@example.com",
            password=self.password,
        )

        self.task = Task.objects.create(
            owner=self.user,
            title="My task",
        )
        self.other_task = Task.objects.create(
            owner=self.other,
            title="Private task",
        )

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "ali", "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}",
        )

        self.list_url = reverse("tasks:task-list")
        self.detail_url = reverse(
            "tasks:task-detail",
            args=[self.task.pk],
        )

    def test_all_task_operations_require_authentication(self):
        self.client.credentials()

        requests = (
            ("get", self.list_url, {}),
            ("post", self.list_url, {"title": "New"}),
            ("get", self.detail_url, {}),
            ("patch", self.detail_url, {"status": "done"}),
            ("delete", self.detail_url, {}),
        )

        for method, url, payload in requests:
            with self.subTest(method=method, url=url):
                response = getattr(self.client, method)(
                    url,
                    payload,
                    format="json",
                )
                self.assertEqual(response.status_code, 401)

    def test_create_sets_owner_and_defaults(self):
        response = self.client.post(
            self.list_url,
            {
                "title": "New task",
                "owner": self.other.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)

        task = Task.objects.get(pk=response.data["id"])

        self.assertEqual(task.owner_id, self.user.pk)
        self.assertEqual(task.status, Task.Status.TODO)
        self.assertEqual(task.priority, Task.Priority.MEDIUM)
        self.assertEqual(task.description, "")
        self.assertIsNone(task.due_date)

    def test_invalid_task_input_is_rejected(self):
        cases = (
            {},
            {"title": ""},
            {"title": "   "},
            {"title": "x" * 201},
            {"title": "Test", "status": "invalid"},
            {"title": "Test", "priority": "invalid"},
            {"title": "Test", "due_date": "not-a-date"},
        )
        initial_count = Task.objects.count()

        for payload in cases:
            with self.subTest(payload=payload):
                response = self.client.post(
                    self.list_url,
                    payload,
                    format="json",
                )
                self.assertEqual(response.status_code, 400, response.data)

        self.assertEqual(Task.objects.count(), initial_count)

    def test_list_contains_only_current_users_tasks(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            [item["id"] for item in response.data["results"]],
            [self.task.pk],
        )

    def test_other_users_task_cannot_be_read_updated_or_deleted(self):
        url = reverse(
            "tasks:task-detail",
            args=[self.other_task.pk],
        )

        for method in ("get", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(
                    url,
                    {"title": "Hacked"},
                    format="json",
                )
                self.assertEqual(response.status_code, 404)

        self.other_task.refresh_from_db()
        self.assertEqual(self.other_task.title, "Private task")
        self.assertEqual(self.other_task.owner_id, self.other.pk)

    def test_retrieve_and_patch_own_task_without_changing_owner(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.task.pk)

        response = self.client.patch(
            self.detail_url,
            {
                "status": "done",
                "owner": self.other.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)

        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.DONE)
        self.assertEqual(self.task.owner_id, self.user.pk)
        self.assertEqual(self.task.title, "My task")

    def test_delete_own_task(self):
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            Task.objects.filter(pk=self.task.pk).exists(),
        )
        self.assertTrue(
            Task.objects.filter(pk=self.other_task.pk).exists(),
        )

    def test_filters_combine_and_preserve_user_isolation(self):
        matching = Task.objects.create(
            owner=self.user,
            title="Matching",
            status=Task.Status.DONE,
            priority=Task.Priority.HIGH,
        )
        Task.objects.create(
            owner=self.user,
            title="Wrong priority",
            status=Task.Status.DONE,
            priority=Task.Priority.LOW,
        )
        Task.objects.create(
            owner=self.other,
            title="Other user's matching task",
            status=Task.Status.DONE,
            priority=Task.Priority.HIGH,
        )

        response = self.client.get(
            self.list_url,
            {"status": "done", "priority": "high"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            [item["id"] for item in response.data["results"]],
            [matching.pk],
        )

    def test_pagination_and_newest_first_ordering(self):
        Task.objects.bulk_create([
            Task(owner=self.user, title=f"Task {number}")
            for number in range(12)
        ])

        expected_ids = list(
            Task.objects.filter(owner=self.user)
            .order_by("-created_at", "-id")
            .values_list("id", flat=True)
        )

        first = self.client.get(self.list_url)
        second = self.client.get(self.list_url, {"page": 2})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)

        self.assertEqual(first.data["count"], 13)
        self.assertEqual(len(first.data["results"]), 10)
        self.assertEqual(len(second.data["results"]), 3)
        self.assertIsNotNone(first.data["next"])
        self.assertIsNone(second.data["next"])

        actual_ids = [
            item["id"]
            for page in (first, second)
            for item in page.data["results"]
        ]
        self.assertEqual(actual_ids, expected_ids)
