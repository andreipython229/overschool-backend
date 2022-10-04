from common_services.models import TimeStampedModel
from django.db import models
from users.models import User

from .course import Course
from .lesson import Lesson
from homeworks.models import Homework
from lesson_tests.models import SectionTest


class UserProgressLogs(TimeStampedModel):
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
        Lesson,
        on_delete=models.CASCADE,
        related_name="user_progresses",
        verbose_name="ID урока",
        help_text="ID урока, который прошёл ученик",
        null=True,
        blank=True
    )
    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name="user_progresses_homework",
        verbose_name="ID дз",
        help_text="ID дз, который прошёл ученик",
        null=True,
        blank=True
    )
    section_test = models.ForeignKey(
        SectionTest,
        on_delete=models.CASCADE,
        related_name="user_progresses_lesson_test",
        verbose_name="ID теста",
        help_text="ID теста, который прошёл ученик",
        null=True,
        blank=True
    )

    def __str__(self) -> str:
        return str(self.user) + " " + str(self.lesson)

    class Meta:
        verbose_name = "Прогресс юзера"
        verbose_name_plural = "Прогрессы юзеров"
