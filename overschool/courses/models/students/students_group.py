from chats.models import Chat
from common_services.mixins import TimeStampMixin
from django.db import models
from users.models.user import User

from .students_group_settings import StudentsGroupSettings
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
        blank=True,
        null=True
    )
    students = models.ManyToManyField(
        User,
        verbose_name="Ученики",
        help_text="Ученики этой группы",
        related_name="students_group_fk",
        blank=True,
    )
    group_settings = models.OneToOneField(
        StudentsGroupSettings,
        on_delete=models.CASCADE,
        related_name='students_group_settings_fk',
        null=True,
        blank=True
    )
    chat = models.OneToOneField(
        Chat,
        on_delete=models.CASCADE,
        related_name='group',
        null=True,
        blank=True
    )
    TYPE_CHOICES = [
        ('WITH_TEACHER', 'С учителем'),
        ('WITHOUT_TEACHER', 'Без учителя'),
    ]

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='WITH_TEACHER',
        verbose_name="Тип группы",
        help_text="Тип группы (С учителем / Без учителя)",
    )

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = "Группа студентов"
        verbose_name_plural = "Группы студентов"
