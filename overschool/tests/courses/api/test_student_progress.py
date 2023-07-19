from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from users.models.user import User


class StudentProgressViewSetTests(APITestCase):
    """Student Progress Lessons"""

    # python manage.py test tests.courses.api.test_student_progress --settings=overschool.settings2

    def setUp(self):
        self.client = APIClient()

        fixture_paths = [
            "users/fixtures/test_initial_role_data.json",
            "schools/fixtures/test_initial_school_data.json",
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
            "schools/fixtures/test_initial_school_header.json",
            "users/fixtures/test_initial_document_data.json",
            "courses/fixtures/test_initial_students_group_data.json",
            "courses/fixtures/test_initial_students_group_settings.json",
        ]
        call_command("loaddata", fixture_paths)

        self.user = User.objects.get(pk=10)
        self.client.force_authenticate(user=self.user)

    def test_get_student_progress_for_student(self):
        url = reverse(
            "student_progress-get-student-progress-for-student", args=["School_1"]
        )
        response = self.client.get(url, {"course_id": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_student_progress_for_teacher(self):
        url = reverse(
            "student_progress-get-student-progress-for-admin-or-teacher",
            args=["School_1"],
        )

        teacher = User.objects.get(pk=5)
        self.client.force_authenticate(user=teacher)

        response = self.client.get(url, {"student_id": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_student_progress_for_admin(self):
        url = reverse(
            "student_progress-get-student-progress-for-admin-or-teacher",
            args=["School_1"],
        )

        admin = User.objects.get(pk=1)
        self.client.force_authenticate(user=admin)

        response = self.client.get(url, {"student_id": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
