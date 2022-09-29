from ckeditor.fields import RichTextField
from common_services.mixins import OrderMixin
from common_services.models import AuthorPublishedModel, TimeStampedModel
from django.db import models
from homeworks.managers import HomeworkManager
from courses.models import Section


class Homework(TimeStampedModel, AuthorPublishedModel, OrderMixin):
    """Модель домашнего задания"""

    homework_id = models.AutoField(
        primary_key=True,
        editable=True,
        verbose_name="ID домашнего задания",
        help_text="Уникальный идентификатор домашнего задания",
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="homeworks",
        verbose_name="Секция",
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Название домашней работы",
        help_text="Домашняя работа по уроку,теме..",
        default="",
    )
    text = RichTextField(
        verbose_name="Описание домашнего задания",
        help_text="HTML вариан описания домашки",
    )
    file = models.FileField(
        upload_to="media/homework/task/files",
        verbose_name="Файл домашнего задания",
        help_text="Файл, в котором хранится вся небходимая информация для домашнего задания",
    )

    objects = HomeworkManager()

    def __str__(self):
        return str(self.homework_id) + " Урок: " + str(self.lesson)

    class Meta:
        verbose_name = "Домашнее задание"
        verbose_name_plural = "Домашние задания"
