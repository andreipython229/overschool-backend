from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class TestUsersList(APITestCase):
    """Проверка API получения списка всех тестов"""

    url_name = "lesson_tests"

    def test_get_countries(self):
        response = self.client.get(reverse(self.url_name), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)