from courses.models.students.students_group import StudentsGroup
from django.db import models
from schools.models import School
from users.models.user import User


class InviteProgram(models.Model):
    is_active = models.BooleanField(
        default=False, verbose_name="Активный", help_text="Активация программы"
    )
    link = models.URLField(
        max_length=255, verbose_name="Ссылка", help_text="Реферальная ссылка", blank=True, null=True
    )
    groups = models.ManyToManyField(
        StudentsGroup, related_name="invite_program", verbose_name="Группы", blank=True
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="invite_program",
        verbose_name="инвайт-программa",
        help_text="инвайт-программa",
    )

    class Meta:
        verbose_name = "инвайт-программа"
        verbose_name_plural = "инвайт-программы"
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["school"]),
        ]

    def __str__(self):
        return f"{self.link} - {self.school}"
