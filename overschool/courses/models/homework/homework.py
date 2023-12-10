from django.db import models
from courses.models import BaseLesson


class Homework(BaseLesson):
    """Модель домашнего задания"""

    homework_id = models.AutoField(
        primary_key=True,
        editable=True,
        verbose_name="ID домашнего задания",
        help_text="Уникальный идентификатор домашнего задания",
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

    class Meta:
        verbose_name = "Домашнее задание"
        verbose_name_plural = "Домашние задания"
        default_related_name = "homeworks"
