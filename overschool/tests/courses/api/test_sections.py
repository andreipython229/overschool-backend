from courses.models.courses.section import Section
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from users.models.user import User


class SectionViewSetAPITestCase(APITestCase):
    """Test Sections"""

    # python manage.py test tests.courses.api.test_sections

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

        self.section = Section.objects.get(pk=5)

    def test_list_section(self):
        url = reverse("sections-list", args=["School_1"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_section(self):
        url = reverse("sections-list", args=["School_1"])
        data = {"order": 10, "name": "New Section", "author": 1, "course": 1}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Section.objects.count(), 6)
        self.assertEqual(response.data["name"], data["name"])

    def test_retrieve_section(self):
        url = reverse("sections-detail", args=["School_1", self.section.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.section.name)

    def test_update_section(self):
        url = reverse("sections-detail", args=["School_1", self.section.pk])
        data = {"order": 10, "name": "New Section Name", "author": 1, "course": 1}
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.section.refresh_from_db()
        self.assertEqual(self.section.name, data["name"])

    def test_partial_update_section(self):
        url = reverse("sections-detail", args=["School_1", self.section.pk])
        data = {"name": "New Section Name"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.section.refresh_from_db()
        self.assertEqual(self.section.name, data["name"])

    def test_delete_section(self):
        url = reverse("sections-detail", args=["School_1", self.section.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Section.objects.filter(pk=self.section.pk).exists())

    def test_list_lessons_by_section(self):
        url = reverse("sections-lessons", args=["School_1", self.section.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
