from common_services.mixins import TimeStampMixin
from django.conf import settings
from django.db import models
from django.utils import timezone

from .section_test import SectionTest


class UserTest(TimeStampMixin, models.Model):
    """Модель сданнаго теста учеником"""

    user_test_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID сданного теста",
        help_text="Уникальный идентификатор сданного теста",
    )
    test = models.ForeignKey(
        SectionTest,
        on_delete=models.CASCADE,
        verbose_name="ID теста",
        related_name="tests",
        help_text="Уникальный идентификатор теста",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
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
    status = models.BooleanField(
        default=False,
        verbose_name="Статус",
        help_text="Статус, отображающий пройден ли тест учеником",
    )
    start_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Время начала теста",
        help_text="Время, когда пользователь начал проходить тест",
    )

    class Meta:
        verbose_name = "Сданный тест"
        verbose_name_plural = "Сданные тесты"

    def start_test(self):
        """Метод для установки времени начала теста"""
        if not self.start_time:
            self.start_time = timezone.now()
            self.save()

    def has_time_left(self):
        """Проверяет, осталось ли у пользователя время на тест"""
        if self.test.has_timer and self.start_time:
            time_elapsed = timezone.now() - self.start_time
            return time_elapsed <= self.test.time_limit
        return True  # Если таймера нет, всегда возвращает True
