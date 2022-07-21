from django.contrib.auth.models import AbstractUser
from django.db import models
from users.managers import UserManager


class User(AbstractUser):
    """User model"""

    user_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID пользователя",
        help_text="Уникальный идентификатор пользователя",
    )
    username = None
    email = models.EmailField("Почта", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email
