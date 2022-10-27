from django.db import models

from common_services.mixins import AuthorMixin, OrderMixin, TimeStampMixin
from courses.models.common.base_lesson import BaseLesson


class BaseLessonFile(TimeStampMixin, AuthorMixin, OrderMixin, models.Model):
    description = models.TextField(
        verbose_name="Описание файла", help_text="Описание файла", null=True, blank=True
    )
    base_lesson = models.ForeignKey(
        BaseLesson, on_delete=models.CASCADE
    )

    class Meta:
        abstract = True
