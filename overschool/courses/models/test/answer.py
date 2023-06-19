from ckeditor.fields import RichTextField
from common_services.mixins import TimeStampMixin
from common_services.services import limit_size
from django.db import models

from .question import Question


class AnswerStatusChoices(models.TextChoices):
    """Варианты статусов для ответов"""


class Answer(TimeStampMixin, models.Model):
    """Модель ответа на вопрос"""

    answer_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID Вопроса",
        help_text="Уникальный идентификатор ответa",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="ID Вопроса",
        help_text="Вопрос, к которому привязан ответ",
    )
    body = RichTextField(verbose_name="Тело ответа", help_text="HTML вариант ответа")
    is_correct = models.BooleanField(
        default=False,
        verbose_name="Тип ответа",
        help_text="Правильный-True или неправильный-False",
    )
    picture = models.ImageField(
        verbose_name="Картинка", validators=[limit_size], null=True, blank=True
    )
    answer_in_range = models.BooleanField(
        default=False,
        verbose_name="Правильный ответ в диапазоне",
        help_text="Характерно для числовых вопросв (Numerical)",
    )
    from_digit = models.BigIntegerField(
        default=0,
        verbose_name="От",
        help_text="В случае, если вопрос числовой (Numerical) и ответ в диапазоне",
    )
    to_digit = models.BigIntegerField(
        default=0,
        verbose_name="До",
        help_text="В случае, если вопрос числовой (Numerical) и ответ в диапазоне",
    )

    def __str__(self):
        return str(self.answer_id) + " " + str(self.body)

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"
