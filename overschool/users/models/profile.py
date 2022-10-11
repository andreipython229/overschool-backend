from common_services.models import TimeStampedModel
from django.db import models
from oauthlib.common import urldecode

from .user import User


class SexChoices(models.TextChoices):
    """Варианты пола пользователя в профиле"""

    MALE = "М", "Мужской"
    FEMALE = "Ж", "Женский"


class Profile(TimeStampedModel):
    """Модель профиля пользователя, создается сигналом при создании пользователя"""

    profile_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID профиля",
        help_text="Уникальный идентификатор профиля",
    )
    avatar = models.ImageField(
        upload_to="images/users/avatar/",
        help_text="Аватар",
        verbose_name="Аватар",
        blank=True,
        null=True,
    )
    city = models.CharField(
        help_text="Город",
        verbose_name="Город",
        max_length=256,
        default="",
    )
    sex = models.CharField(
        max_length=64,
        choices=SexChoices.choices,
        verbose_name="Пол",
        help_text="Пол",
        default="",
    )
    description = models.TextField(
        help_text="О себе",
        verbose_name="О себе",
        default="",
    )
    user = models.OneToOneField(
        User,
        help_text="Пользователь",
        verbose_name="Пользователь",
        related_name="profile",
        on_delete=models.CASCADE,
    )

    def avatar_url(self):
        if self.avatar:
            url = urldecode("https://api.itdev.by" + self.avatar.url)
            return url[0][0]
        return None

    def __str__(self):
        return self.user.username
