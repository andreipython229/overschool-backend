from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from schools.models.school import School
from users.models.user import User


class UserSchoolsTestCase(APITestCase):
    """Тест-кейс эндпоинта user_schools"""

    def setUp(self):
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

        self.client = APIClient()
        self.user = User.objects.first()
        self.client.force_authenticate(user=self.user)

        self.school = School.objects.get(pk=1)

    def test_user_schools_get(self):
        url = reverse("user_schools")
        responce = self.client.get(url)
        self.assertEqual(responce.status_code, status.HTTP_200_OK)
