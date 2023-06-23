from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from users.models.profile import Profile
from users.models.user import User


class ProfileViewSetAPITestCase(APITestCase):
    """Test Profiles"""

    #   python manage.py test tests.users.api.test_profiles

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

        self.profile = Profile.objects.get(pk=1)

    def test_list_profile(self):
        url = reverse("profiles-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_profile(self):
        url = reverse("profiles-detail", args=[self.profile.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["description"], self.profile.description)

    def test_partial_update_profile(self):
        url = reverse("profiles-detail", args=[self.profile.pk])

        patch_data = {
            "city": "string",
            "sex": "М",
            "description": "string",
            "user": {
                "username": "string",
                "first_name": "string",
                "last_name": "string",
                "email": "user@example.com",
                "phone_number": "+375331115159",
                "user": 9,
            },
        }

        response = self.client.patch(url, patch_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
