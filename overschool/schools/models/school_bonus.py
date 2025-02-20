from common_services.mixins import TimeStampMixin
from common_services.services import TruncateFileName, limit_image_size
from courses.models.students.students_group import StudentsGroup
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from schools.models import School


class Bonus(TimeStampMixin, models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="bonuses",
        verbose_name="ID школы",
        help_text="ID школы",
    )
    logo = models.ImageField(
        verbose_name="Логотип",
        help_text="Логотип акции",
        validators=[limit_image_size],
        upload_to=TruncateFileName(300),
        max_length=300,
        blank=True,
        null=True,
    )
    text = models.TextField(
        verbose_name="Описание",
        help_text="Описание акции",
        blank=True,
        null=True,
    )
    link = models.URLField(verbose_name="Ссылка на акцию")
    expire_date = models.DateTimeField(
        verbose_name="Дата и время окончания акции",
        help_text="Дата и время окончания акции",
    )
    active = models.BooleanField(
        default=False,
        verbose_name="Активный",
        help_text="Определяет, активирован ли бонус",
        blank=False,
    )
    student_groups = models.ManyToManyField(
        StudentsGroup,
        verbose_name="Группы",
        help_text="Группы, которым предоставлен бонус",
        related_name="group_bonuses",
        blank=True,
    )
    search_vector = SearchVectorField(blank=True, null=True)

    def __str__(self):
        return f"{self.school} - {self.link}"

    class Meta:
        verbose_name = "Бонус"
        verbose_name_plural = "Бонусы"
        indexes = [
            models.Index(fields=["search_vector"]),
            models.Index(fields=["school"]),
            models.Index(fields=["expire_date"]),
            models.Index(fields=["active"]),
        ]
