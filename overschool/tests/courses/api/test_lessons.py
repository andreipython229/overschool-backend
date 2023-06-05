from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models.user import User
from rest_framework.test import APITestCase
from courses.models.lesson.lesson import Lesson
from django.core.management import call_command

class LessonsViewSetAPITestCase(APITestCase):
    ''' Test Lessons '''
    # python manage.py test tests.courses.api.test_lessons

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
            'courses/fixtures/test_initial_lesson_data.json',
        ]
        call_command('loaddata', fixture_paths)

        self.user = User.objects.first()
        self.client.force_authenticate(user=self.user)

        self.lesson = Lesson.objects.get(pk=1)

    def test_list_lesson(self):
        url = reverse('lessons-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_lesson(self):
        url = reverse('lessons-list')
        data = {
            "section": 1,
            "name": "New Lesson Test",
            "order": 123,
            "description": "Test Lesson Description",
            "video": "",
            "points": 0
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 6)
        self.assertEqual(response.data['name'], data['name'])

    def test_retrieve_lesson(self):
        url = reverse('lessons-detail', args=[self.lesson.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.lesson.name)

    def test_update_lesson(self):
        url = reverse('lessons-detail', args=[self.lesson.pk])
        data = {
            "section": 1,
            "name": "New Lesson Test",
            "order": 123,
            "description": "Test Lesson Description",
            "video": "",
            "points": 0
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.name, data['name'])

    def test_partial_update_lesson(self):
        url = reverse('lessons-detail', args=[self.lesson.pk])
        data = {'name': 'New Lesson Name'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.name, data['name'])

    def test_delete_lesson(self):
        url = reverse('lessons-detail', args=[self.lesson.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Lesson.objects.filter(pk=self.lesson.pk).exists())