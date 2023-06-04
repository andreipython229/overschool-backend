from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models.user import User
from rest_framework.test import APITestCase
from django.core.management import call_command
from courses.models.students.students_table_info import StudentsTableInfo

class StudentsTableInfoViewSetAPITestCase(APITestCase):
    ''' Test Students Table Info '''
    # python manage.py test tests.courses.api.test_students_table_info

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
            'courses/fixtures/test_initial_students_table_info.json'
        ]
        call_command('loaddata', fixture_paths)

        self.user = User.objects.get(pk=1)
        self.client.force_authenticate(user=self.user)

        self.students_table_info = StudentsTableInfo.objects.get(pk=1)

    def test_list_students_table_info(self):
        url = reverse('students_table_info-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_students_table_info(self):
        url = reverse('students_table_info-list')
        data = {
              "admin": 2,
              "students_table_info": [
                  {"id": 1, "order": 1, "name": "Имя", "checked": True},
                  {"id": 2, "order": 2, "name": "Email", "checked": True},
                  {"id": 3, "order": 3, "name": "Суммарный балл", "checked": False},
                  {"id": 4, "order": 4, "name": "Курс", "checked": False},
                  {"id": 5, "order": 5, "name": "Последняя активность", "checked": False},
                  {"id": 6, "order": 6, "name": "Прогресс", "checked": False},
                  {"id": 7, "order": 7, "name": "Комментарий", "checked": True},
                  {"id": 8, "order": 8, "name": "Группа", "checked": False},
                  {"id": 9, "order": 9, "name": "Средний балл", "checked": True},
                  {"id": 10, "order": 10, "name": "Дата обновления", "checked": False},
                  {"id": 11, "order": 11, "name": "Дата заверения", "checked": False}
              ]
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(StudentsTableInfo.objects.count(),2)

    def test_retrieve_students_table_info(self):
        url = reverse('students_table_info-detail', args=[self.students_table_info.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['admin'], self.students_table_info.admin_id)

    def test_update_students_table_info(self):
        url = reverse('students_table_info-detail', args=[self.students_table_info.pk])
        data = {
            "admin": 1,
            "students_table_info": [
                {"id": 1, "order": 1, "name": "Имя", "checked": False},
                {"id": 2, "order": 2, "name": "Email", "checked": True},
            ]
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.students_table_info.refresh_from_db()
        self.assertEqual(self.students_table_info.students_table_info, data['students_table_info'])
    #
    def test_partial_update_students_table_info(self):
        url = reverse('students_table_info-detail', args=[self.students_table_info.pk])
        data = {
            "admin": 2,
            "students_table_info": [
                  {"id": 1, "order": 1, "name": "Имя", "checked": False},
            ]
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.students_table_info.refresh_from_db()
        self.assertEqual(self.students_table_info.admin.pk, data['admin'])
