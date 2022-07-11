from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from lms_Users.database_managers.my_user import MyUserManager


class User(AbstractUser, PermissionsMixin):
    email = models.EmailField('Почта', unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = MyUserManager()

    class Meta:
        app_label = 'lms_Users'

    def __str__(self):
        return self.username
