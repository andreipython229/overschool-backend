from common_services.models import TimeStampedModel
from courses.models import Lesson
from django.db import models


class LessonTest(TimeStampedModel):
    "Модель теста"
    test_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID теста",
        help_text="Уникальный идентификатор теста",
    )
    lesson_id = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="lesson_test_id_fk",
        verbose_name="ID урока",
        help_text="Урок, после которого идёт данный тест",
    )
    name = models.CharField(max_length=256, verbose_name="Название", help_text="Название теста")
    success_percent = models.IntegerField(
        verbose_name="Проходной балл",
        help_text="Процент правильных ответов для успешно пройденного теста",
    )
    random_questions = models.BooleanField(default=False, verbose_name="Перемешать вопросы")
    random_answers = models.BooleanField(default=False, verbose_name="Перемешать ответы")
    show_right_answers = models.BooleanField(default=False, verbose_name="Показать правильные ответы")

    def __str__(self):
        return str(self.test_id) + " " + str(self.name)

    class Meta:
        verbose_name = "Тест"
        verbose_name_plural = "Тесты"
