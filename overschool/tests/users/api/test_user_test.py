from courses.models.test.user_test import UserTest
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from users.models.user import User


class UserTestTestCase(APITestCase):
    """Тест-кейс для эндпоинта usertest"""

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
            "courses/fixtures/test_initial_data_user_test.json",
        ]
        call_command("loaddata", fixture_paths)

        self.user = User.objects.get(pk=1)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.test = UserTest.objects.get(user_test_id=1)

    def test_user_test_get(self):
        url = reverse("test_user-list", args=["School_1"])
        responce = self.client.get(url)
        self.assertEqual(responce.status_code, status.HTTP_200_OK)
