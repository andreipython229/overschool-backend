from django.db import models


class StudentsGroupSettings(models.Model):
    """Модель настроек для группы студентов"""

    strict_task_order = models.BooleanField(
        default=False,
        verbose_name="Строгая последовательность заданий",
        help_text="При 'True' - ученики данной группы не могут открывать уроки не по порядку",
    )
    task_submission_lock = models.BooleanField(
        default=False,
        verbose_name="Блокировка отправки решений заданий",
        help_text="При 'True' - ученики данной группы не могут отправлять домашки, они могут сделать его самостоятельно и перейти к следующему уроку",
    )
    submit_homework_to_go_on = models.BooleanField(
        default=False,
        verbose_name="Необходимость отправки д/з для перехода к следующим урокам",
        help_text="При 'True' - ученики данной группы могут двигаться по курсу дальше только после отправки очередной выполненной домашней работы",
    )
    submit_test_to_go_on = models.BooleanField(
        default=False,
        verbose_name="Необходимость прохождения теста для перехода к следующим урокам",
        help_text="При 'True' - ученики данной группы не могут двигаться по курсу дальше, пока не отправят свой вариант прохождения очередного теста",
    )
    success_test_to_go_on = models.BooleanField(
        default=False,
        verbose_name="Необходимость успешного прохождения теста для перехода к следующим урокам",
        help_text="При 'True' - ученики данной группы не могут двигаться по курсу дальше, пока не наберут необходимый процент правильных ответов очередного теста",
    )
    overai_lock = models.BooleanField(
        default=False,
        verbose_name="Блокировка доступа к OVER AI",
        help_text="При 'True' - OVER AI включен для учеников данной группы",
    )

    def __str__(self):
        return str(self.pk) + " Настройки группы студентов"

    class Meta:
        verbose_name = "Настройки группы студентов"
        verbose_name_plural = "Настройки группы студентов"
