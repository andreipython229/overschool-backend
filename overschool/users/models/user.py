from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from users.managers import UserManager
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework import serializers

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
    confirmation_code = models.CharField(
        verbose_name="Код подтверждения",
        max_length=4,
        null=True,
        blank=True,

    )
    confirmation_code_created_at = models.DateTimeField(
        verbose_name="Дата создания кода подтверждения",
        null=True,
        blank=True,
        default=timezone.now
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

    CONFIRMATION_CODE_EXPIRY_MINUTES = settings.CONFIRMATION_CODE_EXPIRY_MINUTES

    def validate_confirmation_code(self, code):
        # Проверяем время создания кода подтверждения
        expiry_time = datetime.now() - timedelta(minutes=self.CONFIRMATION_CODE_EXPIRY_MINUTES)
        if self.confirmation_code_created_at < expiry_time:
            # Если код просрочен, удаляем его и возвращаем ошибку
            self.confirmation_code = None
            self.confirmation_code_created_at = None
            self.save(update_fields=['confirmation_code', 'confirmation_code_created_at'])
            raise serializers.ValidationError("Confirmation code has expired.")
        else:
            self.confirmation_code_created_at = datetime.now()
            self.save(update_fields=['confirmation_code_created_at'])