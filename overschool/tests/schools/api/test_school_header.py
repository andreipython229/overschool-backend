from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from schools.models.school_header import SchoolHeader
from users.models.user import User


class SchoolHeaderViewSetAPITestCase(APITestCase):
    """Test School Header"""

    #  python manage.py test tests.schools.api.test_school_header

    def setUp(self):
        self.client = APIClient()

        fixture_paths = [
            "users/fixtures/test_initial_role_data.json",
            "users/fixtures/test_initial_user_data.json",
            "schools/fixtures/test_initial_school_data.json",
            "schools/fixtures/test_initial_school_header.json",
            "courses/fixtures/test_initial_course_data.json",
            "courses/fixtures/test_initial_section_data.json",
            "courses/fixtures/test_initial_base_lesson_data.json",
            "courses/fixtures/test_initial_lesson_data.json",
        ]
        call_command("loaddata", fixture_paths)

        self.user = User.objects.first()
        self.client.force_authenticate(user=self.user)

        self.school_header = SchoolHeader.objects.get(pk=1)

    def test_list_school_headers(self):
        url = reverse("school_headers-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_school_headers(self):
        url = reverse("school_headers-list")
        data = {
            "name": "Test SchoolHeader Name",
            "description": "Test Description",
            "school": 1,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SchoolHeader.objects.count(), 6)
        self.assertEqual(response.data["name"], data["name"])

    def test_retrieve_school_headers(self):
        url = reverse("school_headers-detail", args=[self.school_header.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.school_header.name)

    def test_update_school(self):
        url = reverse("school_headers-detail", args=[self.school_header.pk])
        data = {
            "name": "Update Test SchoolHeader Name",
            "description": "Update Test Description",
            "school": 1,
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.school_header.refresh_from_db()
        self.assertEqual(self.school_header.name, data["name"])

    def test_partial_update_school_header(self):
        url = reverse("school_headers-detail", args=[self.school_header.pk])
        data = {"name": "New School Header Name"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.school_header.refresh_from_db()
        self.assertEqual(self.school_header.name, data["name"])

    def test_delete_school(self):
        url = reverse("school_headers-detail", args=[self.school_header.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SchoolHeader.objects.filter(pk=self.school_header.pk).exists())
