from ckeditor.fields import RichTextField
from common_services.mixins import TimeStampMixin
from django.db import models
from model_clone import CloneMixin

from .section_test import SectionTest


class QuestionTypesChoices(models.TextChoices):
    """Варианты типов вопросов"""

    TEXT = "Text", "Text"
    TEXTPICS = "TextPics", "TextPics"
    TEXTPIC = "TextPic", "TextPic"
    FREE = "Free", "Free"
    NUMERICAL = "Numerical", "Numerical"


class Question(TimeStampMixin, CloneMixin, models.Model):
    "Модель вопроса в тесте"

    question_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID Вопроса",
        help_text="Уникальный идентификатор вопроса",
    )
    test = models.ForeignKey(
        SectionTest,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Тест",
        help_text="Тест, к которому привязан вопрос",
    )
    question_type = models.CharField(
        max_length=256,
        choices=QuestionTypesChoices.choices,
        default=QuestionTypesChoices.TEXT,
        verbose_name="Тип",
        help_text="Тип вопроса, от него зависят и возможные поля вопроса",
    )
    body = RichTextField(verbose_name="Вопрос", help_text="Тело вопроса")
    picture = models.ImageField(verbose_name="Картинка", null=True, blank=True)
    is_any_answer_correct = models.BooleanField(
        default=False,
        verbose_name="Любой ответ - правильный",
        help_text="Характерно для вопросов с свободным ответом (FREE)",
    )
    only_whole_numbers = models.BooleanField(
        default=False,
        verbose_name="Только для целых чисел",
        help_text="Характерно для числовых вопросов (Numerical)",
    )
    _clone_m2o_or_o2m_fields = ["answers"]

    def __str__(self):
        return str(self.question_id) + " " + str(self.body)

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
