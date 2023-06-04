from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models.user import User
from rest_framework.test import APITestCase
from django.core.management import call_command
from courses.models.homework.user_homework import UserHomework


class TeacherHomeworkViewSetAPITestCase(APITestCase):
    ''' Test Teacher Homeworks  '''
    # python manage.py test tests.courses.api.test_teacher_homeworks

    def setUp(self):
        self.client = APIClient()

        fixture_paths = [
            'users/fixtures/test_initial_role_data.json',
            'users/fixtures/test_initial_user_data.json',
            'schools/fixtures/test_initial_school_data.json',
            'schools/fixtures/test_initial_school_header.json',
            'courses/fixtures/test_initial_course_data.json',
            'courses/fixtures/test_initial_section_data.json',
            'courses/fixtures/test_initial_base_lesson_data.json',
            'courses/fixtures/test_initial_homework_data.json',
            'courses/fixtures/test_initial_user_homework_data.json',
            'courses/fixtures/test_initial_lesson_data.json',
            'courses/fixtures/test_initial_students_group_data.json',
        ]
        call_command('loaddata', fixture_paths)

        self.user = User.objects.get(pk=5) # user id=5 is Teacher
        self.client.force_authenticate(user=self.user)

        self.user_homework = UserHomework.objects.get(pk=2)

    def test_list_teacher_homeworks(self):
        url = reverse('teacher_homeworks-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_teacher_homework(self):
        url = reverse('teacher_homeworks-detail', args=[self.user_homework.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], self.user_homework.status)

    def test_update_teacher_homework(self):
        url = reverse('teacher_homeworks-detail', args=[self.user_homework.pk])
        data = {
              "homework": 0,
              "status": "На доработке",
              "mark": 2147483647,
              "teacher_message": "string"
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user_homework.refresh_from_db()
        self.assertEqual(self.user_homework.status, data['status'])

    def test_partial_update_teacher_homework(self):
        url = reverse('teacher_homeworks-detail', args=[self.user_homework.pk])
        data = {'status': 'New Status'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user_homework.refresh_from_db()
        self.assertEqual(self.user_homework.status, data['status'])

