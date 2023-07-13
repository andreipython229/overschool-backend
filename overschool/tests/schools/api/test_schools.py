from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from schools.models.school import School
from users.models.user import User


class SchoolsViewSetAPITestCase(APITestCase):
    """Test School"""

    # python manage.py test tests.schools.api.test_schools

    def setUp(self):
        self.client = APIClient()

        fixture_paths = [
            "users/fixtures/test_initial_role_data.json",
            "users/fixtures/test_initial_user_data.json",
            "schools/fixtures/test_initial_school_data.json",
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

        self.school = School.objects.get(pk=1)

    def test_list_school(self):
        url = reverse("schools-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_school(self):
        url = reverse("schools-detail", args=[self.school.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.school.name)

    def test_update_school(self):
        url = reverse("schools-detail", args=[self.school.pk])
        data = {"name": "New Test School Name", "order": 0}
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.school.refresh_from_db()
        self.assertEqual(self.school.name, data["name"])

    def test_partial_update_school(self):
        url = reverse("schools-detail", args=[self.school.pk])
        data = {"name": "New School Name"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.school.refresh_from_db()
        self.assertEqual(self.school.name, data["name"])

    def test_delete_school(self):
        url = reverse("schools-detail", args=[self.school.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(School.objects.filter(pk=self.school.pk).exists())


class SchoolCreateTestCase(APITestCase):
    """Тест-кейс для создания школы"""

    def setUp(self):

        fixture_paths = [
            "users/fixtures/test_initial_role_data.json",
            "users/fixtures/test_initial_user_data.json",
            "schools/fixtures/test_initial_school_data.json",
            "users/fixtures/test_initial_user_group_data.json",
            "schools/fixtures/test_initial_school_header.json",
            "courses/fixtures/test_initial_course_data.json",
            "courses/fixtures/test_initial_section_data.json",
            "courses/fixtures/test_initial_base_lesson_data.json",
            "courses/fixtures/test_initial_lesson_data.json",
        ]
        call_command("loaddata", fixture_paths)

        self.client = APIClient()
        self.user = User.objects.get(pk=5)
        self.client.force_authenticate(user=self.user)

    def test_create_school(self):
        url = reverse("schools-list")
        post_data = {"name": "string", "order": 214748}
        response = self.client.post(url, post_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(School.objects.count(), 6)
        self.assertEqual(response.data["name"], post_data["name"])
