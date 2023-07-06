# from django.core.management import call_command
# from django.urls import reverse
# from rest_framework import status
# from rest_framework.test import APIClient, APITestCase
# from users.models.user import User
# from courses.models.test.user_test import UserTest
#
#
# class UserTestTestCase(APITestCase):
#     """Тест-кейс для эндпоинта usertest"""
#
#     def setUp(self):
#         fixture_paths = [
#             "users/fixtures/test_initial_role_data.json",
#             "users/fixtures/test_initial_user_data.json",
#             "users/fixtures/test_initial_user_group_data.json",
#             "courses/fixtures/test_initial_data_user_test.json",
#             "courses/fixtures/test_initial_section_data.json",
#             "courses/fixtures/test_initial_base_lesson_data.json",
#             "courses/fixtures/test_initial_course_data.json",
#             "courses/fixtures/test_initial_data_answer.json",
#             "courses/fixtures/test_initial_data_question.json",
#             "courses/fixtures/test_initial_data_section_test.json",
#             "courses/fixtures/test_initial_homework_data.json",
#             "courses/fixtures/test_initial_section_data.json",
#             "schools/fixtures/test_initial_school_data.json",
#         ]
#         call_command("loaddata", fixture_paths)
#
#         self.user = User.objects.get(pk=1)
#         self.client = APIClient()
#         self.client.force_authenticate(user=self.user)
#         self.test = UserTest.objects.get(pk=1)
#
#     def test_user_test_get(self):
#         url = reverse('test_user-list', args=["School_1"])
#         responce = self.client.get(url)
#         self.assertEqual(responce.status_code, status.HTTP_200_OK)
#
#     def test_user_test_post(self):
#         url = reverse('test_user-list', args=["School_1"])
#
#         post_data = {
#             "success_percent": "string",
#             "status": False,
#             "test": 123,
#             "user": 15
#         }
#
#         responce = self.client.post(url, post_data, format='json')
#         self.assertEqual(responce.status_code, status.HTTP_201_CREATED)
#
