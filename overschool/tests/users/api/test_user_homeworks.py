import json

from django.core.management import call_command
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status
from django.urls import reverse
from courses.models.homework.user_homework import UserHomework
from users.models.user import User


class UserHomeworksTestCase(APITestCase):
    """Пока не рабочий"""

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

        self.user = User.objects.get(pk=9)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.user_homeworks = UserHomework.objects.get(pk=1)

    def test_user_homeworks_get(self):
        url = reverse('user_homeworks-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_user_homeworks_post(self):
        url = reverse('user_homeworks-list')

        post_data = {
            "homework": 1,
            "text": "string"
        }

        resp = self.client.post(url, post_data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

