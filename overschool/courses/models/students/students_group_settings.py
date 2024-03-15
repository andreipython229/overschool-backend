from django.db import models

class StudentsGroupSettings(models.Model):
    ''' Модель настроек для группы студентов '''

    strict_task_order = models.BooleanField(
        default=False,
        verbose_name="Строгая последовательность заданий",
        help_text="При 'True' - ученики данной группы не могут открывать уроки не по порядку"
    )
    task_submission_lock = models.BooleanField(
        default=False,
        verbose_name="Блокировка отправки решений заданий",
        help_text="При 'True' - ученики данной группы не могут отправлять домашки, они могут сделать его самостоятельно и перейти к следующему уроку"
    )
    overai_lock = models.BooleanField(
        default=False,
        verbose_name="Блокировка доступа к OVER AI",
        help_text="При 'True' - OVER AI включен для учеников данной группы"
    )

    def __str__(self):
        return str(self.pk) + " Настрйки группы студентов"

    class Meta:
        verbose_name = "Настройки группы студентов"
        verbose_name_plural = "Настройки группы студентов"