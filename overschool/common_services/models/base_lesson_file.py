from common_services.mixins import AuthorMixin, OrderMixin, TimeStampMixin
from django.db import models
from overschool.courses.models.base_lesson import BaseLesson


class BaseLessonFile(models.Model, TimeStampMixin, AuthorMixin, OrderMixin):
    title = models.CharField(verbose_name="Название", help_text="Название файла")
    description = models.TextField(verbose_name="Описание файла", help_text="Описание файла", null=True, blank=True)
    lesson = models.ForeignKey(BaseLesson, related_name="files", on_delete=models.CASCADE)

    class Meta:
        abstract = True
