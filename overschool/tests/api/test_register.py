from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class RegisterTestCase(APITestCase):

    def test_missing_fields(self):
        url = reverse('register')
        invalid_data = {
            'email': 'testuser@test.com',
            'password': 'password123',
        }
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_email(self):
        url = reverse('register')
        invalid_data = {
            'email': 'testuser',
            'phone_number': '+375258769022',
            'password': 'password123',
            'password_confirmation': 'password123'
        }
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_mismatch(self):
        url = reverse('register')
        invalid_data = {
            'email': 'testuser@test.com',
            'phone_number': '+375258769022',
            'password': 'password123',
            'password_confirmation': 'mismatchedpassword'
        }
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
