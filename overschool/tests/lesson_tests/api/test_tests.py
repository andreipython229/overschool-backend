import json

from django.core.management import call_command
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status
from django.urls import reverse
from courses.models.test.section_test import SectionTest
from users.models.user import User


class TestsTestCase(APITestCase):

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

        self.test = SectionTest.objects.get(pk=2)

    def test_tests_get(self):
        url = reverse('tests-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_tests_id_get(self):
        url = reverse('tests-detail', args=[self.test.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_tests_post(self):
        url = reverse('tests-list')

        post_data = {
            "section": 1,
            "name": "string",
            "success_percent": 2147483647,
            "random_questions": True,
            "random_answers": True,
            "show_right_answers": True,
            "attempt_limit": True,
            "attempt_count": 2147483647,
            "points_per_answer": 2147483647,
            "points": 21,
            "order": 33
        }

        resp = self.client.post(url, post_data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_tests_put(self):
        url = reverse('tests-detail', args=[self.test.pk])

        put_data = {
            "section": 1,
            "name": "string",
            "success_percent": 2147483647,
            "random_questions": True,
            "random_answers": True,
            "show_right_answers": True,
            "attempt_limit": True,
            "attempt_count": 2147483647,
            "points_per_answer": 2147483647,
            "points": 21,
            "order": 21
        }

        resp = self.client.put(url, put_data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_tests_patch(self):
        url = reverse('tests-detail', args=[self.test.pk])

        patch_data = {
            "section": 1,
            "name": "string",
            "success_percent": 2147483647,
            "random_questions": True,
            "random_answers": True,
            "show_right_answers": True,
            "attempt_limit": True,
            "attempt_count": 2147483647,
            "points_per_answer": 2147483647,
            "points": 21,
            "order": 21
        }

        resp = self.client.patch(url, patch_data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_tests_delete(self):
        url = reverse('tests-detail', args=[self.test.pk])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_tests_id_get_questions_get(self):
        url = '/api/tests/3/get_questions/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)