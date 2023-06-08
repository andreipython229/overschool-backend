import json

from django.core.management import call_command
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status
from django.urls import reverse
from users.models.user import User


class RegisterSchoolOwnerTestCase(APITestCase):

    def setUp(self):
        fixture_paths = [
            'courses/fixtures/test_initial_base_lesson_data.json',
            'courses/fixtures/test_initial_course_data.json',
            'courses/fixtures/test_initial_data_answer.json',
            'courses/fixtures/test_initial_data_question.json',
            'courses/fixtures/test_initial_data_section_test.json',
            # 'courses/fixtures/test_initial_data_user_test.json',
            'courses/fixtures/test_initial_homework_data.json',
            'courses/fixtures/test_initial_lesson_data.json',
            'courses/fixtures/test_initial_section_data.json',
            'courses/fixtures/test_initial_students_group_data.json',
            # 'courses/fixtures/test_initial_students_group_students_data.json',
            'courses/fixtures/test_initial_user_progress_data.json',
            'courses/fixtures/test_initial_user_homework_data.json',
            'schools/fixtures/test_initial_school_data.json',
            'schools/fixtures/test_initial_school_header.json',
            'users/fixtures/test_initial_document_data.json',
            # 'users/fixtures/test_initial_profile_data.json',
            'users/fixtures/test_initial_role_data.json',
            'users/fixtures/test_initial_user_data.json'
        ]

        call_command('loaddata', fixture_paths)

        self.user = User.objects.get(pk=1)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_register_school_owner_post(self):
        url = reverse('register_school_owner')

        post_data = {
            "email": "admin@example.com",
            "phone_number": "+375445769005",
            "password": "admin",
            "password_confirmation": "admin"
        }

        resp = self.client.post(url, post_data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)