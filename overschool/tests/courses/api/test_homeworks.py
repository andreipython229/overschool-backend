from users.models.user import User
from courses.models.homework.homework import Homework
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models.user import User
from users.admin.user import UserAdmin
from rest_framework.test import APITestCase


class AllUserHomeworkTestCase(APITestCase):

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

        self.user = User.objects.first()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_all_user_homework(self):
        url = reverse("all_user_homework-list")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_get_all_user_homeworks_id(self):
        url = reverse("all_user_homework-list".format(2))
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class HomeworksTestCase(APITestCase):

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

        self.user = User.objects.first()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.homework = Homework.objects.get(pk=1)

    def test_homeworks_get(self):
        url = reverse("homeworks-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_homeworks_id_get(self):
        url = reverse('homeworks-detail', args=[self.homework.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_homeworks_post(self):
        url = reverse('homeworks-list')

        post_data = {
            "section": 1,
            "name": "string",
            "order": 2147483647,
            "description": "string",
            "video": "",
            "automate_accept": True,
            "time_accept": "",
            "points": 2147483647
        }

        responce = self.client.post(url, post_data, format='json')
        self.assertEqual(responce.status_code, status.HTTP_201_CREATED)

    def test_homeworks_put(self):
        url = reverse('homeworks-detail', args=[self.homework.pk])

        put_data = {
            "section": 1,
            "name": "string",
            "order": 45,
            "description": "string",
            "video": "",
            "automate_accept": True,
            "time_accept": "",
            "points": 21
        }

        resp = self.client.put(url, put_data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_homeworks_patch(self):
        url = reverse('homeworks-detail', args=[self.homework.pk])

        patch_data = {
            "section": 1,
            "name": "string",
            "order": 45,
            "description": "string",
            "video": "",
            "automate_accept": True,
            "time_accept": "",
            "points": 21
        }

        resp = self.client.patch(url, patch_data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_homeworks_delete(self):
        url = reverse('homeworks-detail', args=[self.homework.pk])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)


class HomeworksStatsTestCase(APITestCase):
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

        self.user = User.objects.first()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_homeworks_stats_get(self):
        url = reverse('homeworks_stats-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)