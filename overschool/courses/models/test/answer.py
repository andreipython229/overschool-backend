from ckeditor.fields import RichTextField
from common_services.mixins import TimeStampMixin
from django.db import models

from .question import Question


class AnswerStatusChoices(models.TextChoices):
    """Варианты статусов для ответов"""

    INCORRECT = "П", "Правильный"
    CORRECT = "Н", "Неправильный"


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
    status = models.CharField(
        max_length=256,
        choices=AnswerStatusChoices.choices,
        default=AnswerStatusChoices.INCORRECT,
        verbose_name="Тип ответа",
        help_text="Тип ответа: Правильный или неправильный или ещё какой",
    )
    picture = models.ImageField(
        upload_to="files/answers", verbose_name="Картинка", null=True, blank=True
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
