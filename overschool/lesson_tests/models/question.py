from ckeditor.fields import RichTextField
from common_services.models import TimeStampedModel
from django.db import models

from .section_test import LessonTest


class Question(TimeStampedModel):
    "Модель вопроса в тесте"
    question_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID Вопроса",
        help_text="Уникальный идентификатор вопроса",
    )
    test = models.ForeignKey(
        LessonTest,
        on_delete=models.CASCADE,
        related_name="question_test_id_fk",
        verbose_name="Тест",
        help_text="Тест, к которому привязан вопрос",
    )
    body = RichTextField(verbose_name="Вопрос", help_text="Тело вопроса")

    def __str__(self):
        return str(self.question_id) + " " + str(self.body)

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
