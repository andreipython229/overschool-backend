from common_services.mixins import TimeStampMixin
from django.db import models
from users.models.user import User

from .students_group import StudentsGroup


class TrainingDuration(TimeStampMixin, models.Model):
    """
    Модель продолжительности обучения студентов в группах
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="training_duration",
        verbose_name="ID ученика",
        help_text="ID ученика",
    )

    students_group = models.ForeignKey(
        StudentsGroup,
        on_delete=models.CASCADE,
        verbose_name="Группа студентов",
        help_text="Группа студентов",
    )

    limit = models.PositiveIntegerField(
        verbose_name="Продолжительность обучения",
        help_text="Лимит продолжительности обучения в днях",
        default=0,
    )

    download = models.BooleanField(
        default=False,
        verbose_name="Возможность скачивания видео",
        help_text="При 'True' - ученик может скачивать видео-уроки в процессе обучения в данной группе",
    )

    def __str__(self):
        return f"{self.user} {self.students_group}"

    class Meta:
        verbose_name = "Продолжительность и иные особенности обучения"
        verbose_name_plural = "Продолжительность и иные особенности обучения"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["students_group"]),
        ]
