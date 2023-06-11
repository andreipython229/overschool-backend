from django.db import models

from common_services.mixins import TimeStampMixin
from users.models.user import User

from ..courses.course import Course


class StudentsGroup(TimeStampMixin, models.Model):
    """
    Модель группы студентов
    """

    group_id = models.AutoField(
        primary_key=True,
        editable=True,
        verbose_name="Группа ID",
        help_text="Уникальный идентификатор группы",
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Название группы",
        help_text="Название группы",
    )
    course_id = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name="Курс",
        help_text="Курс, который проходит эта группа",
        related_name="group_course_fk",
    )
    teacher_id = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Преподаватель",
        help_text="Преподаватель, который ведёт эту группу",
        related_name="teacher_group_fk",
    )
    students = models.ManyToManyField(
        User,
        verbose_name="Ученики",
        help_text="Ученики этой группы",
        related_name="students_group_fk",
    )
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

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = "Группа студентов"
        verbose_name_plural = "Группы студентов"
