from datetime import datetime, timedelta

import jwt
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from overschool import settings
from phonenumber_field.modelfields import PhoneNumberField
from users.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Модель пользователя"""

    user_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID пользователя",
        help_text="Уникальный идентификатор пользователя",
    )
    username = models.CharField(verbose_name="Имя пользователя", max_length=150, unique=True)
    first_name = models.CharField(verbose_name="Имя", max_length=150, null=True, blank=True)
    last_name = models.CharField(verbose_name="Фамилия", max_length=150, null=True, blank=True)
    patronymic = models.CharField(verbose_name="Отчество", max_length=150, null=True, blank=True)
    email = models.EmailField(verbose_name="Почта", help_text="Почта", null=True, blank=True)
    phone_number = PhoneNumberField(verbose_name="Номер телефона", help_text="Номер телефона", null=True, blank=True)
    is_staff = models.BooleanField(verbose_name="Админ", default=False)
    is_active = models.BooleanField(verbose_name="Активный", default=True)
    date_joined = models.DateTimeField(verbose_name="Дата регистрации", default=timezone.now)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "phone_number"]

    objects = UserManager()

    @property
    def token(self):
        return self._generate_jwt_token()

    def get_full_name(self):
        return f"{self.last_name} {self.first_name} {self.patronymic}"

    def get_short_name(self):
        return f"{self.first_name} {self.last_name}"

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def _generate_jwt_token(self):
        """
        Генерирует веб-токен JSON, в котором хранится идентификатор этого
        пользователя, срок действия токена составляет 1 день от создания
        """
        dt = datetime.now() + timedelta(days=1)

        token = jwt.encode({"id": self.pk, "exp": int(dt.strftime("%s"))}, settings.SECRET_KEY, algorithm="HS256")

        return token

    def __str__(self):
        return f"{self.username} ({self.email or self.phone_number})"
