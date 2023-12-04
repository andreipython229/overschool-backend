from django.db import models
from users.models.user import User
from .students_group import StudentsGroup


class StudentsHistory(models.Model):
    """
    Модель истории добавления, удаления студентов в группах
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_history",
        verbose_name="ID ученика",
        help_text="ID ученика",
    )

    students_group = models.ForeignKey(
        StudentsGroup,
        on_delete=models.CASCADE,
        related_name="students_group",
        verbose_name="Группа студентов",
        help_text="Группа студентов",
    )

    date_added = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата добавления в группу",
        help_text="Дата добавления в группу",
    )

    date_removed = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата удаления из группы",
        help_text="Дата удаления из группы",
    )

    is_deleted = models.BooleanField(
        default=False,
        verbose_name="Студент удален из группы",
        help_text="Студент удален из группы",
    )

    def __str__(self):
        return f'{self.user} {self.students_group}'

    class Meta:
        verbose_name = "Student history"
        verbose_name_plural = "Student history"
