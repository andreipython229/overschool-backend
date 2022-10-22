from django.db import models

from common_services.mixins import AuthorMixin, OrderMixin, TimeStampMixin
from overschool.courses.models.common.base_lesson import BaseLesson


class BaseLessonFile(TimeStampMixin, AuthorMixin, OrderMixin, models.Model):
    title = models.CharField(verbose_name="Название", help_text="Название файла")
    description = models.TextField(
        verbose_name="Описание файла", help_text="Описание файла", null=True, blank=True
    )
    lesson = models.ForeignKey(
        BaseLesson, related_name="files", on_delete=models.CASCADE
    )

    class Meta:
        abstract = True
