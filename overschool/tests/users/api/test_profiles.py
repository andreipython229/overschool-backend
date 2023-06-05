from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models.user import User
from users.models.profile import Profile
from rest_framework.test import APITestCase
from django.core.management import call_command


class ProfileViewSetAPITestCase(APITestCase):
    ''' Test Profiles '''
    #   python manage.py test tests.users.api.test_profiles

    def setUp(self):
        self.client = APIClient()

        fixture_paths = [
            'users/fixtures/test_initial_role_data.json',
            'users/fixtures/test_initial_user_data.json',
            'schools/fixtures/test_initial_school_data.json',
            'schools/fixtures/test_initial_school_header.json',
            'schools/fixtures/test_initial_school_user_data.json',
            'courses/fixtures/test_initial_course_data.json',
            'courses/fixtures/test_initial_section_data.json',
            'courses/fixtures/test_initial_base_lesson_data.json',
            'courses/fixtures/test_initial_lesson_data.json',
        ]
        call_command('loaddata', fixture_paths)

        self.user = User.objects.first()
        self.client.force_authenticate(user=self.user)

        self.profile = Profile.objects.get(pk=1)

    def test_list_profile(self):
        url = reverse('profiles-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_profile(self):
        url = reverse('profiles-detail', args=[self.profile.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], self.profile.description)

    def test_partial_update_profile(self):
        url = reverse('profiles-detail', args=[self.profile.pk])
        data = {'description': 'New Profile Description'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.description, data['description'])

    def test_delete_profile(self):
        url = reverse('profiles-detail', args=[self.profile.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Profile.objects.filter(pk=self.profile.pk).exists())