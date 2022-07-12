from django.db import models

from courses.models import Lesson
from overschool.abstract_models import TimeStampedModel
from users.models import SchoolUser

from .homework import Homework


class UserHomeworkStatusChoices(models.TextChoices):
    """
    Варианты статусов для ответа на домашнее задание
    """

    ARRIVE = "ПРИ", "Пришёл"
    CHECKED = "ПРО", "Проверен"
    FAILED = "НЕП", "Неправильно"
    SUCCESS = "ПРА", "Правильно"


class UserHomework(TimeStampedModel):
    """
    Модель выполненной домашки юзером, здесь будут храниться его ответы и комменты препода
    """

    user_homework_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID выполненного домашнего задания",
        help_text="Уникальный идентификатор выполненной домашней работы",
    )
    user_id = models.ForeignKey(
        SchoolUser,
        on_delete=models.SET_DEFAULT,
        default=1,
        related_name="user_homework_user_id_fk",
        verbose_name="ID ученика",
        help_text="ID ученика, выолнившего домашнюю работу",
    )
    homework_id = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name="user_homework_homework_id_fk",
        verbose_name="ID домашнего задания",
        help_text="ID домашнего задания, ответ на который прислали",
    )
    teacher_id = models.ForeignKey(
        SchoolUser,
        on_delete=models.SET_DEFAULT,
        default=1,
        related_name="user_homework_teacher_id_fk",
        verbose_name="ID учителя",
        help_text="Учитель, который проверял домашнюю работы",
        null=True,
    )
    text = models.TextField(
        verbose_name="Ответ ученика", help_text="Ответ ученика на домашнее задание"
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

    def __str__(self):
        return str(self.user_homework_id) + " " + str(self.user_id)

    class Meta:
        verbose_name = "Сданная домашка"
        verbose_name_plural = "Сданные домашки"
