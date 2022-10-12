from common_services.mixins import TimeStampMixin
from django.db import models
from homeworks.models import Homework
from lesson_tests.models import SectionTest
from overschool.courses.models.base_lesson import BaseLesson
from users.models import User

from .course import Course
from .lesson import Lesson


class UserProgressLogs(models.Model, TimeStampMixin):
    """Модель для отслеживания прогресса пользователя"""

    user_progress_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID прогресса",
        help_text="Уникальный идентификатор прогресса",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_progresses",
        verbose_name="ID ученика",
        help_text="ID ученика по прогрессу на курсе",
    )
    lesson = models.ForeignKey(
        BaseLesson,
        on_delete=models.CASCADE,
        related_name="user_progresses",
        verbose_name="ID урока/дз/теста",
        help_text="ID урока/дз/теста, который был завершен",
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return str(self.user) + " " + str(self.lesson)

    class Meta:
        verbose_name = "Прогресс юзера"
        verbose_name_plural = "Прогрессы юзеров"
