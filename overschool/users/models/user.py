from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from users.managers import UserManager


class User(AbstractUser):
    """Модель пользователя"""

    user_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID пользователя",
        help_text="Уникальный идентификатор пользователя",
    )
    email = models.EmailField(verbose_name="Почта", help_text="Почта", null=True, blank=True)
    phone_number = PhoneNumberField(verbose_name="Номер телефона", help_text="Номер телефона", null=True, blank=True)

    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.username
