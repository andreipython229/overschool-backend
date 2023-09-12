from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from users.models.user import User


class UserTestCAse(APITestCase):
    """Проверка API получения данных пользователя"""

    def setUp(self):
        self.client = APIClient()

        fixture_paths = [
            "users/fixtures/test_initial_role_data.json",
            "schools/fixtures/test_initial_school_data.json",
            "users/fixtures/test_initial_user_data.json",
            "users/fixtures/test_initial_user_group_data.json",
            "schools/fixtures/test_initial_school_header.json",
            "courses/fixtures/test_initial_course_data.json",
            "courses/fixtures/test_initial_section_data.json",
            "courses/fixtures/test_initial_base_lesson_data.json",
            "courses/fixtures/test_initial_lesson_data.json",
        ]
        call_command("loaddata", fixture_paths)

        self.user = User.objects.first()
        self.client.force_authenticate(user=self.user)

    def test_user_get(self):
        url = reverse("user-list")
        responce = self.client.get(url)
        self.assertEqual(responce.status_code, status.HTTP_200_OK)

    def test_user_id_get(self):
        url = reverse("user-detail", args=[self.user.pk])
        responce = self.client.get(url)
        self.assertEqual(responce.status_code, status.HTTP_200_OK)
