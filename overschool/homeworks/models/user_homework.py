from common_services.models import TimeStampedModel
from django.db import models
from oauthlib.common import urldecode
from users.models import User
from .homework import Homework


class UserHomeworkStatusChoices(models.TextChoices):
    """Варианты статусов для ответа на домашнее задание"""

    ARRIVE = "На доработке", "На доработке"
    CHECKED = "Ждет проверки", "Ждет проверки"
    FAILED = "Отклонено", "Отклонено"
    SUCCESS = "Принято", "Принято"


class UserHomework(TimeStampedModel):
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
    text = models.TextField(
        verbose_name="Ответ ученика",
        help_text="Ответ ученика на домашнее задание",
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=256,
        choices=UserHomeworkStatusChoices.choices,
        default=UserHomeworkStatusChoices.ARRIVE,
        verbose_name="Статус",
        help_text="Статус отправленной домашки",
    )
    file = models.FileField(
        upload_to="media/homework/task/answers",
        verbose_name="Файл ответа",
        help_text="Файл, в котором содержится ответ на домашнюю работу",
        null=True,
        blank=True,
    )
    mark = models.IntegerField(
        verbose_name="Отметка",
        help_text="Отметка за домашнюю работу",
        null=True,
        blank=True,
    )
    teacher_message = models.TextField(
        verbose_name="Комментарий",
        help_text="Комментарий преподавателя по проделанной работе",
        null=True,
        blank=True,
    )

    def file_url(self):
        if self.file:
            url = urldecode("https://api.itdev.by" + self.file.url)
            return url[0][0]
        return None

    def __str__(self):
        return str(self.user_homework_id) + " " + str(self.user_id)

    class Meta:
        verbose_name = "Сданная домашка"
        verbose_name_plural = "Сданные домашки"
