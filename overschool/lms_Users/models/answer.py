from ckeditor.fields import RichTextField
from django.db import models

from .time_stamped_model import TimeStampedModel
from .question import Question


class AnswerStatusChoices(models.TextChoices):
    "Варианты статусов для ответов"
    INCORRECT = 'П', 'Правильный'
    CORRECT = 'Н', 'Неправильный'


class Answer(TimeStampedModel):
    "Модель ответа на вопрос"
    answer_id = models.AutoField(primary_key=True, editable=False,
                                 verbose_name="ID Вопроса",
                                 help_text="Уникальный идентификатор вопроса")
    question_id = models.ForeignKey(Question, on_delete=models.CASCADE,
                                    related_name="question_answer_id_fk",
                                    verbose_name="ID Вопроса",
                                    help_text="Вопрос, к которому привязан ответ")
    body = RichTextField(verbose_name="Тело ответа",
                         help_text="HTML вариант ответа")
    status = models.CharField(max_length=256, choices=AnswerStatusChoices.choices,
                              default=AnswerStatusChoices.INCORRECT,
                              verbose_name="Тип ответа",
                              help_text="Тип ответа: Правильный или неправильный или ещё какой"
                              )

    def __str__(self):
        return str(self.answer_id)+" "+str(self.body)

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"

