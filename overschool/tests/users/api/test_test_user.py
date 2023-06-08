import json

from django.core.management import call_command
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status
from django.urls import reverse
from users.models.user import User
from courses.models.test.user_test import UserTest


class UserTestsTestCase(APITestCase):
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

        self.user = User.objects.get(pk=10)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.user_test = UserTest.objects.filter(user_test_id=2)

    def test_test_user_get(self):
        url = reverse('test_user-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_test_user_id_get(self):
        url = reverse('test_user-list', args=[self.user_test.user_test_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_test_user_post(self):
        url = reverse('test_user-list')

        post_data = {
            "success_percent": "string",
            "status": "П",
            "test": 2,
            "user": 10
        }

        resp = self.client.post(url, post_data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_test_user_put(self):
        url = reverse('test_user-detail', args=[self.user_test.pk])

        put_data = {
            "success_percent": "string",
            "status": "П",
            "test": 2,
            "user": 3
        }

        resp = self.client.put(url, put_data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)