from common_services.models import TimeStampedModel
from django.db import models
from users.models import User

from .course import Course
from .lesson import Lesson


class UserProgress(TimeStampedModel):
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
        help_text="ID курса, на котором сейчас находится ученик, если None значит,"
        "урок был удалён, либо ученик только начал",
    )

    def __str__(self) -> str:
        return str(self.user) + " " + str(self.lesson)

    class Meta:
        verbose_name = "Прогресс юзера"
        verbose_name_plural = "Прогрессы юзеров"
