from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from users.managers import SchoolUserManager


class SchoolUser(AbstractUser, PermissionsMixin):
    email = models.EmailField('Почта', unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = SchoolUserManager()

    class Meta:
        app_label = 'users'

    def __str__(self):
        return self.username
