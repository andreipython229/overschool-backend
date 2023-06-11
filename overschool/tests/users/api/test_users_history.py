from django.core.management import call_command
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status
from django.urls import reverse
from users.models.user import User


class UsersHistoryTestCase(APITestCase):

    def setUp(self):
        fixture_paths = [
            'courses/fixtures/test_initial_course_data.json',
            'courses/fixtures/test_initial_section_data.json',
            'schools/fixtures/test_initial_school_data.json',
            'users/fixtures/test_initial_role_data.json',
            'users/fixtures/test_initial_user_data.json'
        ]

        call_command('loaddata', fixture_paths)

        self.user = User.objects.get(pk=1)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_users_history_get(self):
        url = reverse('user_history-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)