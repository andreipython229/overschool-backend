from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.db import models


class MyUserManager(BaseUserManager):

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Вы не ввели Email")
        user = self.model(
            email=self.normalize_email(email),
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password):
        return self._create_user(email, password, is_staff=False)

    def create_superuser(self, email, password):
        return self._create_user(email, password, is_staff=True, is_superuser=True)


class User(AbstractUser, PermissionsMixin):
    email = models.EmailField('Почта', unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = MyUserManager()

    def __str__(self):
        return self.username
