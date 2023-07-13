from courses.models.test.answer import Answer
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework.views import status
from users.models.user import User


class AnswersTestCase(APITestCase):
    def setUp(self):
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
            "courses/fixtures/test_initial_section_data.json",
        ]

        call_command("loaddata", fixture_paths)

        self.user = User.objects.get(pk=1)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.answer = Answer.objects.get(pk=2)

    def test_answers_get(self):
        url = reverse("answers-list", args=["School_1"])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_answers_id_get(self):
        url = reverse("answers-detail", args=["School_1", self.answer.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_answers_create_post(self):
        url = reverse("answers-list", args=["School_1"])

        post_data = {
            "body": 2,
            "is_correct": True,
            "answer_in_range": True,
            "from_digit": 1000,
            "to_digit": 1010,
            "question": 2,
        }

        responce = self.client.post(url, post_data, format="json")
        self.assertEqual(responce.status_code, status.HTTP_201_CREATED)

    def test_answers_put(self):
        url = reverse("answers-detail", args=["School_1", self.answer.pk])

        put_data = {
            "body": "string",
            "is_correct": True,
            "answer_in_range": True,
            "from_digit": 10045,
            "to_digit": 11000,
            "question": 3,
        }

        resp = self.client.put(url, put_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_answers_patch(self):
        url = reverse("answers-detail", args=["School_1", self.answer.pk])

        patch_data = {
            "body": "string",
            "is_correct": True,
            "answer_in_range": False,
            "from_digit": 920,
            "to_digit": 950,
            "question": 5,
        }

        resp = self.client.patch(url, patch_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_answers_delete(self):
        url = reverse("answers-detail", args=["School_1", self.answer.pk])
        resp = self.client.delete(url, self.answer.pk, format="json")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
