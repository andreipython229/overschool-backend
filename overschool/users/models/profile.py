from common_services.models import TimeStampedModel
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from .user import User


class SexChoices(models.TextChoices):
    """Варианты пола пользователя в профиле"""

    MALE = "М", "Мужской"
    FEMALE = "Ж", "Женский"


class Profile(User, TimeStampedModel):
    """Модель профиля пользователя, создается сигналом при создании пользователя"""

    avatar = models.ImageField(
        upload_to="images/users/avatar/",
        help_text="Аватар",
        verbose_name="Аватар",
    )
    phone_number = PhoneNumberField(help_text="Номер телефона", verbose_name="Номер телефона", null=True, blank=True)
    city = models.CharField(help_text="Город", verbose_name="Город", max_length=256, null=True, blank=True)
    sex = models.CharField(
        max_length=64,
        choices=SexChoices.choices,
        verbose_name="Пол",
        null=True,
        blank=True,
        help_text="Пол",
    )
    description = models.TextField(help_text="О себе", verbose_name="О себе", null=True, blank=True)

    def __str__(self):
        return self.email
