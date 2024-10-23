from chats.models import Chat
from common_services.mixins import TimeStampMixin
from django.db import models
from users.models.user import User

from ..courses.course import Course
from .students_group_settings import StudentsGroupSettings


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
        null=True,
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
        related_name="students_group_settings_fk",
        null=True,
        blank=True,
    )
    chat = models.OneToOneField(
        Chat, on_delete=models.CASCADE, related_name="group", null=True, blank=True
    )
    TYPE_CHOICES = [
        ("WITH_TEACHER", "С учителем"),
        ("WITHOUT_TEACHER", "Без учителя"),
    ]

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default="WITH_TEACHER",
        verbose_name="Тип группы",
        help_text="Тип группы (С учителем / Без учителя)",
    )
    certificate = models.BooleanField(
        default=False,
        verbose_name="Доступ к сертификатам",
        help_text="Могут ли участники этой группы видеть сертификаты",
    )
    training_duration = models.PositiveIntegerField(
        verbose_name="Продолжительность обучения",
        help_text="Лимит продолжительности обучения в днях",
        default=0,
    )

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = "Группа студентов"
        verbose_name_plural = "Группы студентов"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["course_id"]),
            models.Index(fields=["teacher_id"]),
            models.Index(fields=["group_id"]),
        ]


class GroupCourseAccess(models.Model):
    current_group = models.ForeignKey(
        StudentsGroup,
        on_delete=models.CASCADE,
        related_name="current_group_accesses",
        verbose_name="Текущая группа",
        help_text="Группа, для которой предоставлен доступ к курсу",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name="Курс",
        help_text="Курс, к которому предоставлен доступ",
    )
    group = models.ForeignKey(
        StudentsGroup,
        on_delete=models.CASCADE,
        related_name="group_accesses",
        verbose_name="Новая группа на курсе",
        help_text="Группа на курсе, на которую предоставлен доступ",
    )

    def __str__(self):
        return f"{self.current_group} -> {self.course} -> {self.group}"

    class Meta:
        verbose_name = "Доступ к курсу для группы"
        verbose_name_plural = "Доступы к курсам для групп"
        indexes = [
            models.Index(fields=["current_group"]),
            models.Index(fields=["course"]),
            models.Index(fields=["group"]),
        ]
