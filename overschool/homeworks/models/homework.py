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
        default="Имя не придумано",
    )
    description = RichTextField(
        verbose_name="Описание домашнего задания",
        help_text="HTML вариан описания домашки",
        blank=True,
        null=True,
    )
    file = models.FileField(
        upload_to="media/homework/task/files",
        verbose_name="Файл домашнего задания",
        help_text="Файл, в котором хранится вся небходимая информация для домашнего задания",
        blank=True,
        null=True,
    )
    balls = models.PositiveIntegerField(
        verbose_name="Кол-во баллов за урок",
        help_text="Кол-во баллов за урок",
        default=0,
    )
    automate_accept = models.BooleanField(
        verbose_name="Автоматически принимать работы спустя время",
        help_text="После отправки учеником работы спустя указанное кол-во времени"
                  "будет автоматически поставлен зачёт",
        default=False,
    )
    time_accept = models.DurationField(
        verbose_name="Поставить зачёт через",
        help_text="Время через которое будет автоматически поставлен зачёт, формат: [DD] [HH:[MM:]]ss[.uuuuuu]",
        blank=True,
        null=True,
    )
    objects = HomeworkManager()

    def file_url(self):
        if self.file:
            return "https://api.itdev.by" + self.file.url
        return None

    def __str__(self):
        return str(self.homework_id)

    class Meta:
        verbose_name = "Домашнее задание"
        verbose_name_plural = "Домашние задания"
