from courses.models.test.question import Question
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework.views import status
from users.models.user import User


class QuestionsTestCase(APITestCase):
    def setUp(self):
        fixture_paths = [
            "users/fixtures/test_initial_role_data.json",
            "schools/fixtures/test_initial_school_data.json",
            "users/fixtures/test_initial_user_data.json",
            "users/fixtures/test_initial_user_group_data.json",
            "courses/fixtures/test_initial_base_lesson_data.json",
            "courses/fixtures/test_initial_course_data.json",
            "courses/fixtures/test_initial_data_question.json",
            "courses/fixtures/test_initial_data_section_test.json",
            "courses/fixtures/test_initial_homework_data.json",
            "courses/fixtures/test_initial_section_data.json",
        ]

        call_command("loaddata", fixture_paths)

        self.user = User.objects.get(pk=1)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.question = Question.objects.get(pk=2)

    def test_questions_get(self):
        url = reverse("questions-list", args=["School_1"])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_questions_id_get(self):
        url = reverse("questions-detail", args=["School_1", self.question.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_questions_post(self):
        url = reverse("questions-list", args=["School_1"])

        post_data = {
            "question_type": "Text",
            "body": "string",
            "is_any_answer_correct": True,
            "only_whole_numbers": True,
            "test": 1,
        }

        resp = self.client.post(url, post_data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_questions_put(self):
        url = reverse("questions-detail", args=["School_1", self.question.pk])

        put_data = {
            "question_type": "Text",
            "body": "string",
            "is_any_answer_correct": True,
            "only_whole_numbers": True,
            "test": 3,
        }

        resp = self.client.put(url, put_data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_questions_patch(self):
        url = reverse("questions-detail", args=["School_1", self.question.pk])

        patch_data = {
            "question_type": "Text",
            "body": "string",
            "is_any_answer_correct": True,
            "only_whole_numbers": True,
            "test": 3,
        }

        resp = self.client.patch(url, patch_data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_questions_delete(self):
        url = reverse("questions-detail", args=["School_1", self.question.pk])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
