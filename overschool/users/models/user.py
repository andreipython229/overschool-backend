from datetime import datetime, timedelta

import jwt
from django.contrib.auth.models import AbstractUser
from django.db import models
from users.managers import UserManager

from overschool import settings


class User(AbstractUser):
    """Модель пользователя"""

    user_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID пользователя",
        help_text="Уникальный идентификатор пользователя",
    )
    username = None
    email = models.EmailField(verbose_name="Почта", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    @property
    def token(self):
        return self._generate_jwt_token()

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    def _generate_jwt_token(self):
        """
        Генерирует веб-токен JSON, в котором хранится идентификатор этого
        пользователя, срок действия токена составляет 1 день от создания
        """
        dt = datetime.now() + timedelta(days=1)

        token = jwt.encode({
            'id': self.pk,
            'exp': int(dt.strftime('%s'))
        }, settings.SECRET_KEY, algorithm='HS256')

        return token

    def __str__(self):
        return self.email
