from django.db import models

from courses.models.students.students_group import StudentsGroup


class SchoolMeetings(models.Model):

    students_groups = models.ManyToManyField(StudentsGroup, related_name='school_meetings')
    link = models.URLField(verbose_name='Ссылка для перехода на митинг')
    start_date = models.DateTimeField(verbose_name="Дата и время начала миттинга", help_text="Дата и время начала миттинга")

    class Meta:
        verbose_name = 'Ссылка на митинг'
        verbose_name_plural = 'Ссылки на митинг'




