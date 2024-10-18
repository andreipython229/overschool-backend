from common_services.mixins import TimeStampMixin
from courses.models import Course
from django.db import models
from users.models import User

from .homework import Homework


class UserHomeworkStatusChoices(models.TextChoices):
    """Варианты статусов для ответа на домашнее задание"""

    CHECKED = "Ждет проверки", "Ждет проверки"
    FAILED = "Отклонено", "Отклонено"
    SUCCESS = "Принято", "Принято"


class UserHomework(TimeStampMixin, models.Model):
    """Модель выполненной домашки юзером, здесь будут храниться его ответы и комменты препода"""

    user_homework_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID выполненного домашнего задания",
        help_text="Уникальный идентификатор выполненной домашней работы",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_homeworks",
        verbose_name="ID ученика",
        help_text="ID ученика, выполнившего домашнюю работу",
    )
    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name="user_homeworks",
        verbose_name="ID домашнего задания",
        help_text="ID домашнего задания, ответ на который прислали",
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="teacher_homeworks",
        verbose_name="ID учителя",
        help_text="Учитель, который проверял домашнюю работы",
    )
    copy_course_id = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name="ID копии курса",
        help_text="ID копии курса, если домашка относится к копии курса",
        blank=True,
        null=True,
        default=None,
    )
    text = models.TextField(
        verbose_name="Ответ ученика",
        help_text="Ответ ученика на домашнее задание",
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
        return str(self.user_homework_id) + " " + str(self.user_id)

    class Meta:
        verbose_name = "Сданная домашка"
        verbose_name_plural = "Сданные домашки"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["homework"]),
            models.Index(fields=["teacher"]),
            models.Index(fields=["mark"]),
            models.Index(fields=["status"]),
        ]
