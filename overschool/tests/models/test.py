from django.db import models
from courses.models import Lesson

from overschool.abstract_models import TimeStampedModel


class Test(TimeStampedModel):
    "Модель теста"
    test_id = models.AutoField(primary_key=True, editable=False,
                               verbose_name="ID Теста",
                               help_text="Уникальный идентификатор теста")
    lesson_id = models.ForeignKey(Lesson, on_delete=models.CASCADE,
                                  related_name="lesson_test_id_fk",
                                  verbose_name="ID урока",
                                  help_text="Урок, после которого идёт данный тест")
    name = models.CharField(max_length=256, verbose_name="Название",
                            help_text="Название теста")
    success_percent = models.IntegerField(verbose_name="Проходной балл",
                                          help_text="Процент правильных ответов для успешно пройденного теста")

    def __str__(self):
        return str(self.test_id)+" "+str(self.name)

    class Meta:
        verbose_name = "Тест"
        verbose_name_plural = "Тесы"
