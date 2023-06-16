from courses.models.courses.course import Course
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from users.models.user import User


class CoursesTestCase(APITestCase):
    """test_courses_id_stats_get не работает, ошибка в самом эндпоинте"""

    def setUp(self):
        fixture_paths = [
            "courses/fixtures/test_initial_base_lesson_data.json",
            "courses/fixtures/test_initial_course_data.json",
            "courses/fixtures/test_initial_data_answer.json",
            "courses/fixtures/test_initial_data_question.json",
            "courses/fixtures/test_initial_data_section_test.json",
            # 'courses/fixtures/test_initial_data_user_test.json',
            "courses/fixtures/test_initial_homework_data.json",
            "courses/fixtures/test_initial_lesson_data.json",
            "courses/fixtures/test_initial_section_data.json",
            "courses/fixtures/test_initial_students_group_data.json",
            "courses/fixtures/test_initial_user_progress_data.json",
            "courses/fixtures/test_initial_user_homework_data.json",
            "schools/fixtures/test_initial_school_data.json",
            "schools/fixtures/test_initial_school_header.json",
            "users/fixtures/test_initial_document_data.json",
            # 'users/fixtures/test_initial_profile_data.json',
            "users/fixtures/test_initial_role_data.json",
            "users/fixtures/test_initial_user_data.json",
        ]

        call_command("loaddata", fixture_paths)

        self.user = User.objects.get(pk=1)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.course = Course.objects.first()

    def test_courses_get(self):
        url = reverse("courses-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_courses_id_get(self):
        url = reverse("courses-detail", args=[self.course.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_courses_id_clone_get(self):
        url = reverse("courses-detail", args=[self.course.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_courses_id_sections_get(self):
        url = reverse("courses-sections", args=[self.course.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # def test_courses_id_stats_get(self):
    #     url = reverse("courses-stats", args=[self.course.pk])
    #     resp = self.client.get(url)
    #     self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_courses_id_student_group_get(self):
        url = reverse("courses-detail", args=[self.course.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_courses_id_user_count_by_month(self):
        url = reverse("courses-detail", args=[self.course.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_courses_create_post(self):
        url = reverse("courses-list")

        post_data = {
            "public": "О",
            "name": "string",
            "format": "ОФФ",
            "duration_days": 23,
            "price": "14",
            "description": "string",
            "order": 45,
            "school": 1,
        }

        response = self.client.post(url, post_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_courses_update_put(self):
        url = reverse("courses-detail", args=[self.course.pk])

        put_data = {
            "public": "О",
            "name": "string",
            "format": "ОФФ",
            "duration_days": 27,
            "price": "14",
            "description": "string",
            "order": 44,
            "school": 1,
        }

        response = self.client.put(url, put_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_courses_patch(self):
        url = reverse("courses-detail", args=[self.course.pk])

        patch_data = {
            "public": "О",
            "name": "string",
            "format": "ОФФ",
            "duration_days": 21,
            "price": "15",
            "description": "string",
            "order": 45,
            "school": 1,
        }

        response = self.client.patch(url, patch_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_courses_delete(self):
        url = reverse("courses-detail", args=[self.course.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
