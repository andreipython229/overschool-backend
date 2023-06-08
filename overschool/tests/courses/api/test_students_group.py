from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models.user import User
from rest_framework.test import APITestCase
from django.core.management import call_command
from courses.models.students.students_group import StudentsGroup

class StudentsGroupViewSetAPITestCase(APITestCase):
    ''' Test Students Group  '''
    # python manage.py test tests.courses.api.test_students_group

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
            'courses/fixtures/test_initial_students_group_data.json',
        ]
        call_command('loaddata', fixture_paths)

        self.user = User.objects.first()
        self.client.force_authenticate(user=self.user)

        self.students_group = StudentsGroup.objects.get(pk=1)

    def test_list_lesson(self):
        url = reverse('students_group-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_students_group(self):
        url = reverse('students_group-list')
        data = {
              "name": "Students Group Name",
              "course_id": 1,
              "teacher_id": 1,
              "students": [1]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(StudentsGroup.objects.count(),3)
        self.assertEqual(response.data['name'], data['name'])

    def test_retrieve_students_group(self):
        url = reverse('students_group-detail', args=[self.students_group.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.students_group.name)

    def test_update_students_group(self):
        url = reverse('students_group-detail', args=[self.students_group.pk])
        data = {
            "name": "New Students Group Name",
            "course_id": 1,
            "teacher_id": 1,
            "students": [1]
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.students_group.refresh_from_db()
        self.assertEqual(self.students_group.name, data['name'])

    def test_partial_update_students_group(self):
        url = reverse('students_group-detail', args=[self.students_group.pk])
        data = {'name': 'New Students Group Name'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.students_group.refresh_from_db()
        self.assertEqual(self.students_group.name, data['name'])

    def test_delete_students_group(self):
        url = reverse('students_group-detail', args=[self.students_group.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(StudentsGroup.objects.filter(pk=self.students_group.pk).exists())