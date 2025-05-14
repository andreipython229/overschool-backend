from courses.models.students.students_group import StudentsGroup
from django.db import models


class SchoolMeetings(models.Model):
    students_groups = models.ManyToManyField(
        StudentsGroup, related_name="school_meetings"
    )
    link = models.URLField(verbose_name="Ссылка для перехода на митинг")
    description = models.TextField(
        verbose_name="Описание миттинга", blank=True, null=True
    )
    title = models.CharField(
        verbose_name="Название миттинга", max_length=500, blank=True, null=True
    )
    start_date = models.DateTimeField(
        verbose_name="Дата и время начала миттинга",
        help_text="Дата и время начала миттинга",
    )

    class Meta:
        verbose_name = "Ссылка на митинг"
        verbose_name_plural = "Ссылки на митинг"
        indexes = [models.Index(fields=["start_date"])]
