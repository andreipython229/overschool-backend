from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.urls import reverse
from rest_framework import status

from tests.services.auth_admin_test_case import AuthAdminTestCase
from users.models import SchoolUser


class TestUsersAdmin(AuthAdminTestCase):
    def test_users_changelist(self):
        """Проверка получения списка пользователей в админке"""
        response = self.client.get(
            reverse(admin_urlname(SchoolUser._meta, "changelist")), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_users_change(self):
        """Проверка получения страницы пользователя с id=1 в админке"""
        response = self.client.get(
            reverse(admin_urlname(SchoolUser._meta, "change"), args=[1]), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_users_delete(self):
        """Проверка удаления страницы пользователя с id=1 в админке"""
        response = self.client.get(
            reverse(admin_urlname(SchoolUser._meta, "delete"), args=[1]), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
