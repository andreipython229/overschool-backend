from ckeditor.fields import RichTextField
from django.db import models

from .time_stamped_model import TimeStampedModel
from .lesson import Lesson


class Homework(TimeStampedModel):
    "Модель домашнего задания"
    homework_id = models.AutoField(primary_key=True, editable=True,
                                   verbose_name="ID домашнего задания",
                                   help_text="Уникальный идентификатор домашнего задания")
    lesson_id = models.ForeignKey(Lesson, on_delete=models.CASCADE,
                                  related_name="homework_lesson_id_fk",
                                  verbose_name="Домашнее задание",
                                  )
    text = RichTextField(verbose_name="Описание домашнего задания",
                         help_text="HTML вариан описания домашки")
    file = models.FileField(upload_to="media/homework/task/files",
                            verbose_name="Файл домашнего задания",
                            help_text="Файл, в котором хранится вся небходимая информация для домашнего задания")

    def __str__(self):
        return str(self.homework_id)+" Урок: "+str(self.lesson_id)

    class Meta:
        verbose_name = "Домашнее задание"
        verbose_name_plural = "Домашние задания"

