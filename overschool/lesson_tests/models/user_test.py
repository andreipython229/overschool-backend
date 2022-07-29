from common_services.models import TimeStampedModel
from django.db import models
from users.models import User

from .lesson_test import LessonTest


class UserTestStatusChoices(models.TextChoices):
    """Варианты статусов для пройденного теста"""

    SUCCESS = "П", "Прошёл"
    FAILED = "Н", "Не прошёл"


class UserTest(TimeStampedModel):
    """Модель сданнаго теста учеником"""

    user_test_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID сданного теста",
        help_text="Уникальный идентификатор сданного теста",
    )
    test = models.ForeignKey(
        LessonTest,
        on_delete=models.CASCADE,
        verbose_name="ID теста",
        related_name="tests",
        help_text="Уникальный идентификатор теста",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        default=1,
        verbose_name="ID пользователя",
        related_name="users",
        help_text="Уникальный идентификатор пользователя",
    )
    success_percent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Процент(%) правильных ответов",
        help_text="Процент правильных ответов, которые ввёл ученик ученик",
    )
    status = models.CharField(
        max_length=256,
        choices=UserTestStatusChoices.choices,
        default=UserTestStatusChoices.SUCCESS,
        verbose_name="Статус",
        help_text="Статус, отображающий пройден ли тест учеником",
    )

    class Meta:
        verbose_name = "Сданный тест"
        verbose_name_plural = "Сданные тесты"
