from common_services.mixins import AuthorMixin, OrderMixin, TimeStampMixin
from courses.models.common.base_lesson import BaseLesson
from courses.models.homework.user_homework import UserHomework
from courses.models.homework.user_homework_check import UserHomeworkCheck
from django.db import models


class BaseLessonFile(TimeStampMixin, AuthorMixin, OrderMixin, models.Model):
    description = models.TextField(
        verbose_name="Описание файла", help_text="Описание файла", null=True, blank=True
    )
    base_lesson = models.ForeignKey(
        BaseLesson,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    user_homework = models.ForeignKey(
        UserHomework,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    user_homework_check = models.ForeignKey(
        UserHomeworkCheck,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True
