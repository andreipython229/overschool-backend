from common_services.models import TimeStampedModel
from django.db import models
from users.models import User

from .course import Course
from .lesson import Lesson


class UserProgress(TimeStampedModel):
    """
    Модель для отслеживания прогресса пользователя
    """

    user_id = models.ForeignKey(
        User,
        on_delete=models.SET_DEFAULT,
        default=1,
        related_name="user_progress_user_id_fk",
        verbose_name="ID ученика",
        help_text="ID ученика по прогрессу на курсе",
    )
    course_id = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="user_progress_course_id_fk",
        verbose_name="ID курса",
        help_text="ID курса, который сейчас проходит ученик",
    )
    lesson_id = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        related_name="user_progress_lesson_id_fk",
        verbose_name="ID урока",
        null=True,
        help_text="ID курса, на котором сейчас находится ученик, если None значит,"
        "урок был удалён, либо ученик только начал",
    )

    class Meta:
        verbose_name = "Прогресс юзера"
        verbose_name_plural = "Прогрессы юзеров"
