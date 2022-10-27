from ast import Assert

from django.test import TestCase

from users.models import User


class UserTestCase(TestCase):
    def test_create_user(self):
        """Check create_user successful"""
        User.objects.create_user(
            username="normuser", email="user@example.com", password="user"
        )

    def test_create_superuser(self):
        """Check create_superuser successful"""
        User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin"
        )
