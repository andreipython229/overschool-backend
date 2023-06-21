from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from users.managers import UserManager


class User(AbstractBaseUser):
    """Модель пользователя"""

    id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID пользователя",
        help_text="Уникальный идентификатор пользователя",
    )
    username = models.CharField(
        verbose_name="Имя пользователя",
        max_length=150,
        unique=True,
        null=True,
        blank=True,
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=150,
        default="",
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=150,
        default="",
    )
    patronymic = models.CharField(
        verbose_name="Отчество",
        max_length=150,
        default="",
    )
    email = models.EmailField(
        verbose_name="Почта", help_text="Почта", null=True, blank=True
    )
    phone_number = PhoneNumberField(
        verbose_name="Номер телефона", help_text="Номер телефона", null=True, blank=True
    )
    is_staff = models.BooleanField(verbose_name="Админ", default=False)
    is_active = models.BooleanField(verbose_name="Активный", default=False)
    is_superuser = models.BooleanField(verbose_name="Superuser status", default=False)
    date_joined = models.DateTimeField(
        verbose_name="Дата регистрации", default=timezone.now
    )

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["email", "phone_number"]

    objects = UserManager()

    def has_perm(self, perm, obj=None):
        if self.is_active and self.is_superuser:
            return True

    def has_module_perms(self, app_label):
        if self.is_active and self.is_superuser:
            return True

    def __str__(self):
        return f"{self.username} ({self.email or self.phone_number})"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
