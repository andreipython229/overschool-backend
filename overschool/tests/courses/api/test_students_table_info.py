from courses.models.students.students_table_info import StudentsTableInfo
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from users.models.user import User


class StudentsTableInfoViewSetAPITestCase(APITestCase):
    """Test Students Table Info"""

    # python manage.py test tests.courses.api.test_students_table_info

    def setUp(self):
        self.client = APIClient()

        fixture_paths = [
            "users/fixtures/test_initial_role_data.json",
            "schools/fixtures/test_initial_school_data.json",
            "users/fixtures/test_initial_user_data.json",
            "users/fixtures/test_initial_user_group_data.json",
            "schools/fixtures/test_initial_school_header.json",
            "courses/fixtures/test_initial_course_data.json",
            "courses/fixtures/test_initial_section_data.json",
            "courses/fixtures/test_initial_base_lesson_data.json",
            "courses/fixtures/test_initial_lesson_data.json",
            "courses/fixtures/test_initial_students_group_data.json",
            "courses/fixtures/test_initial_students_group_settings.json",
        ]
        call_command("loaddata", fixture_paths)

        self.user = User.objects.get(pk=1)
        self.client.force_authenticate(user=self.user)

        self.students_table_info = StudentsTableInfo.objects.get(pk=1)

    def test_list_students_table_info(self):
        url = reverse("students_table_info-list", args=["School_1"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_students_table_info(self):
        url = reverse(
            "students_table_info-detail", args=["School_1", self.students_table_info.pk]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["admin"], self.students_table_info.admin_id)

    def test_update_students_table_info(self):
        url = reverse(
            "students_table_info-detail", args=["School_1", self.students_table_info.pk]
        )
        data = {
            "admin": 1,
            "students_table_info": [
                {"id": 1, "order": 1, "name": "Имя", "checked": True},
                {"id": 2, "order": 2, "name": "Email", "checked": True},
            ],
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.students_table_info.refresh_from_db()
        self.assertEqual(
            self.students_table_info.students_table_info, data["students_table_info"]
        )
