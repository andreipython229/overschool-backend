from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models.user import User
from rest_framework.test import APITestCase
from django.core.management import call_command
from courses.models.students.students_group import StudentsGroup
from courses.models.students.students_group_settings import StudentsGroupSettings

class StudentsGroupViewSetAPITestCase(APITestCase):
    ''' Test Students Group  '''
    # python manage.py test tests.courses.api.test_students_group

    def setUp(self):
        fixture_paths = [
            "users/fixtures/test_initial_role_data.json",
            "users/fixtures/test_initial_user_data.json",
            "users/fixtures/test_initial_user_group_data.json",
            "courses/fixtures/test_initial_base_lesson_data.json",
            "courses/fixtures/test_initial_course_data.json",
            "courses/fixtures/test_initial_data_answer.json",
            "courses/fixtures/test_initial_data_question.json",
            "courses/fixtures/test_initial_data_section_test.json",
            "courses/fixtures/test_initial_homework_data.json",
            "courses/fixtures/test_initial_lesson_data.json",
            "courses/fixtures/test_initial_section_data.json",
            "courses/fixtures/test_initial_user_progress_data.json",
            "schools/fixtures/test_initial_school_data.json",
            "schools/fixtures/test_initial_school_header.json",
            "users/fixtures/test_initial_document_data.json",
            'courses/fixtures/test_initial_students_group_data.json',
            'courses/fixtures/test_initial_students_group_settings.json'
        ]
        call_command('loaddata', fixture_paths)

        self.client = APIClient()
        self.user = User.objects.first()
        self.client.force_authenticate(user=self.user)

        self.students_group = StudentsGroup.objects.get(pk=1)

    def test_list_lesson(self):
        url = reverse('students_group-list', args=["School_1"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_students_group(self):
        url = reverse('students_group-list', args=["School_1"])
        post_data = {
            "name": "string",
            "course_id": 3,
            "teacher_id": 5,
            "students": [
                3
            ]
        }
        response = self.client.post(url, post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_retrieve_students_group(self):
        url = reverse('students_group-detail', args=["School_1", self.students_group.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.students_group.name)

    def test_update_students_group(self):
        url = reverse('students_group-detail', args=["School_1", self.students_group.pk])
        put_data = {
            "group_settings": {
                "strict_task_order": True,
                "task_submission_lock": True
            },
            "name": "string",
            "course_id": 1,
            "teacher_id": 5,
            "students": [
                2
            ]
        }
        response = self.client.put(url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_partial_update_students_group(self):
        url = reverse('students_group-detail', args=["School_1", self.students_group.pk])
        patch_data = {
            "group_settings": {
                "strict_task_order": True,
                "task_submission_lock": True
            },
            "name": "string",
            "course_id": 1,
            "teacher_id": 5,
            "students": [
                2
            ]
        }
        response = self.client.patch(url, patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_students_group(self):
        url = reverse('students_group-detail', args=["School_1", self.students_group.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(StudentsGroup.objects.filter(pk=self.students_group.pk).exists())


class StudentsGroupSettingsTestCase(APITestCase):
    """Тест-кейс для эндпоинта students_group_settings"""

    def setUp(self):
        fixture_paths = [
            "users/fixtures/test_initial_role_data.json",
            "users/fixtures/test_initial_user_data.json",
            "users/fixtures/test_initial_user_group_data.json",
            "courses/fixtures/test_initial_base_lesson_data.json",
            "courses/fixtures/test_initial_course_data.json",
            "courses/fixtures/test_initial_data_answer.json",
            "courses/fixtures/test_initial_data_question.json",
            "courses/fixtures/test_initial_data_section_test.json",
            "courses/fixtures/test_initial_homework_data.json",
            "courses/fixtures/test_initial_lesson_data.json",
            "courses/fixtures/test_initial_section_data.json",
            "courses/fixtures/test_initial_user_progress_data.json",
            "schools/fixtures/test_initial_school_data.json",
            "schools/fixtures/test_initial_school_header.json",
            "users/fixtures/test_initial_document_data.json",
            'courses/fixtures/test_initial_students_group_data.json',
            'courses/fixtures/test_initial_students_group_settings.json',
        ]

        call_command('loaddata', fixture_paths)

        self.client = APIClient()
        self.user = User.objects.first()
        self.client.force_authenticate(user=self.user)

        self.students_group = StudentsGroup.objects.get(pk=1)
        self.students_group_settings = StudentsGroupSettings.objects.get(pk=1)

    def test_students_group_settings_get(self):
        url = reverse('students_group_settings-list', args=["School_1"])
        responce = self.client.get(url)
        self.assertEqual(responce.status_code, status.HTTP_200_OK)