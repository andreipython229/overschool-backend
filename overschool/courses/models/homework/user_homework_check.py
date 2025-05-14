from common_services.mixins import AuthorMixin, TimeStampMixin
from django.db import models

from .user_homework import UserHomework, UserHomeworkStatusChoices


class UserHomeworkCheck(TimeStampMixin, AuthorMixin, models.Model):
    """Модель истории проверки домашки юзера, здесь будут храниться его ответы и комменты препода"""

    user_homework_check_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID истории проверки домашнего задания",
        help_text="Уникальный идентификатор проверки домашней работы",
    )
    user_homework = models.ForeignKey(
        UserHomework,
        on_delete=models.CASCADE,
        related_name="user_homework_checks",
        verbose_name="ID домашнего задания студента",
        help_text="ID домашнего задания, ответ на который прислали",
    )
    text = models.TextField(
        verbose_name="Ответ ученика или учителя",
        help_text="Ответ ученика или учителя на домашнее задание",
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=256,
        choices=UserHomeworkStatusChoices.choices,
        default=UserHomeworkStatusChoices.CHECKED,
        verbose_name="Статус",
        help_text="Статус отправленной домашки",
    )
    mark = models.IntegerField(
        verbose_name="Отметка",
        help_text="Отметка за домашнюю работу",
        null=True,
        blank=True,
    )

    def __str__(self):
        return str(self.user_homework) + " " + str(self.status)

    class Meta:
        verbose_name = "История проверки домашки юзера"
        verbose_name_plural = "Истории проверки домашки юзера"
        indexes = [
            models.Index(fields=["user_homework"]),
            models.Index(fields=["status"]),
            models.Index(fields=["mark"]),
        ]
