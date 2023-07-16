from ..common.base_lesson import BaseLesson
from django.db import models


class Lesson(BaseLesson):
    """Модель урока в разделе"""

    lesson_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID Урока",
        help_text="Уникальный идентификатор урока",
    )

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        default_related_name = "lessons"