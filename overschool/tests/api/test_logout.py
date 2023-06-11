from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from users.models.user import User


class LogOutTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.first()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_logout(self):
        url = reverse('logout')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)