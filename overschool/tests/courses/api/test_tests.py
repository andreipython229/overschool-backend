from courses.models.test.section_test import SectionTest
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from users.models.user import User


class TestsTestCase(APITestCase):
    """Тест-кейс для эднопинта tests"""

    def setUp(self):
        fixture_paths = [
            "users/fixtures/test_initial_role_data.json",
            "schools/fixtures/test_initial_school_data.json",
            "users/fixtures/test_initial_user_data.json",
            "users/fixtures/test_initial_user_group_data.json",
            "courses/fixtures/test_initial_base_lesson_data.json",
            "courses/fixtures/test_initial_course_data.json",
            "courses/fixtures/test_initial_data_answer.json",
            "courses/fixtures/test_initial_data_question.json",
            "courses/fixtures/test_initial_data_section_test.json",
            "courses/fixtures/test_initial_homework_data.json",
            "courses/fixtures/test_initial_lesson_data.json",
            "courses/fixtures/test_initial_section_data.json",
            "courses/fixtures/test_initial_user_progress_data.json",
            "schools/fixtures/test_initial_school_header.json",
            "users/fixtures/test_initial_document_data.json",
        ]

        call_command("loaddata", fixture_paths)

        self.user = User.objects.get(pk=1)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.test = SectionTest.objects.get(pk=1)

    def test_tests_get(self):
        url = reverse("tests-list", args=["School_1"])
        responce = self.client.get(url)
        self.assertEqual(responce.status_code, status.HTTP_200_OK)

    def test_tests_id_get(self):
        url = reverse("tests-detail", args=["School_1", self.test.pk])
        responce = self.client.get(url)
        self.assertEqual(responce.status_code, status.HTTP_200_OK)

    def test_tests_id_get_questions_get(self):
        url = reverse("tests-detail", args=["School_1", self.test.pk])
        responce = self.client.get(url)
        self.assertEqual(responce.status_code, status.HTTP_200_OK)

    def test_tests_post(self):
        url = reverse("tests-list", args=["School_1"])

        post_data = {
            "section": 1,
            "name": "string",
            "success_percent": 2147483647,
            "random_questions": True,
            "random_answers": True,
            "show_right_answers": True,
            "attempt_limit": True,
            "attempt_count": 2147483647,
            "points_per_answer": 2147483647,
            "points": 2147483647,
            "order": 21474,
        }

        responce = self.client.post(url, post_data)
        self.assertEqual(responce.status_code, status.HTTP_201_CREATED)

    def test_tests_put(self):
        url = reverse("tests-detail", args=["School_1", self.test.pk])

        put_data = {
            "section": 1,
            "name": "string",
            "success_percent": 2147483647,
            "random_questions": True,
            "random_answers": True,
            "show_right_answers": True,
            "attempt_limit": True,
            "attempt_count": 2147483647,
            "points_per_answer": 2147483647,
            "points": 2147483647,
            "order": 21474874,
        }

        responce = self.client.put(url, put_data)
        self.assertEqual(responce.status_code, status.HTTP_200_OK)

    def test_tests_patch(self):
        url = reverse("tests-detail", args=["School_1", self.test.pk])

        patch_data = {
            "section": 1,
            "name": "string",
            "success_percent": 2147483647,
            "random_questions": True,
            "random_answers": True,
            "show_right_answers": True,
            "attempt_limit": True,
            "attempt_count": 2147483647,
            "points_per_answer": 2147483647,
            "points": 2147483647,
            "order": 21474874,
        }

        responce = self.client.patch(url, patch_data)
        self.assertEqual(responce.status_code, status.HTTP_200_OK)

    def test_tests_delete(self):
        url = reverse("tests-detail", args=["School_1", self.test.pk])
        responce = self.client.delete(url)
        self.assertEqual(responce.status_code, status.HTTP_204_NO_CONTENT)
