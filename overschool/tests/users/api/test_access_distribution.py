from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from schools.models.school import School
from users.models.user import User


class AccessDistributionTestCase(APITestCase):
    """Тест-кейс для эндпоинта access-distribution"""

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

        self.user = User.objects.first()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.school = School.objects.get(pk=1)

    def test_access_distribution_post(self):
        url = reverse("access_distribution", args=["School_1"])

        post_data = {"user_id": 31, "role": "Student", "student_groups": [1]}

        responce = self.client.post(url, post_data)
        self.assertEqual(responce.status_code, status.HTTP_201_CREATED)

    # def test_access_distribution_delete(self):
    #     url = reverse('access_distribution', args=["School_1"])
    #     responce = self.client.delete(url)
    #     self.assertEqual(responce.status_code, status.HTTP_204_NO_CONTENT)
