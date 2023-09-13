# import json
#
# from django.core.management import call_command
# from django.urls import reverse
# from rest_framework import status
# from rest_framework.test import APIClient, APITestCase
# from users.models.user import User
#
#
# class LoginTestCase(APITestCase):
#
#     def setUp(self):
#         fixture_paths = [
#             "courses/fixtures/test_initial_base_lesson_data.json",
#             "courses/fixtures/test_initial_course_data.json",
#             "courses/fixtures/test_initial_data_answer.json",
#             "courses/fixtures/test_initial_data_question.json",
#             "courses/fixtures/test_initial_data_section_test.json",
#             # 'courses/fixtures/test_initial_data_user_test.json',
#             "courses/fixtures/test_initial_homework_data.json",
#             "courses/fixtures/test_initial_lesson_data.json",
#             "courses/fixtures/test_initial_section_data.json",
#             # "courses/fixtures/test_initial_students_group_data.json",
#             "courses/fixtures/test_initial_user_progress_data.json",
#             # "courses/fixtures/test_initial_user_homework_data.json",
#             "schools/fixtures/test_initial_school_data.json",
#             "schools/fixtures/test_initial_school_header.json",
#             "users/fixtures/test_initial_document_data.json",
#             # 'users/fixtures/test_initial_profile_data.json',
#             "users/fixtures/test_initial_role_data.json",
#             "users/fixtures/test_initial_user_data.json",
#         ]
#
#         call_command("loaddata", fixture_paths)
#
#         self.user = User.objects.get(pk=1)
#         self.client = APIClient()
#
#     # def test_login_success(self):
#     #     url = reverse("login")
#     #     post_data = {
#     #         "login": "admin@gmail.com",
#     #         "password": "admin"
#     #     }
#     #     resp = self.client.post(url, post_data, format="json")
#     #     self.assertEqual(resp.status_code, status.HTTP_200_OK)
#
#     # def test_login_invalid_credentials(self):
#     #     response = self.client.post(
#     #         reverse("login"),
#     #         data=json.dumps(self.invalid_payload),
#     #         content_type="application/json",
#     #     )
#     #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#     #     self.assertNotIn("access", response.cookies)
#     #     self.assertNotIn("refresh", response.cookies)
#
#     def test_login_missing_credentials(self):
#         response = self.client.post(
#             reverse("login"),
#             data=json.dumps({"email": "", "password": ""}),
#             content_type="application/json",
#         )
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertNotIn("access", response.cookies)
#         self.assertNotIn("refresh", response.cookies)
