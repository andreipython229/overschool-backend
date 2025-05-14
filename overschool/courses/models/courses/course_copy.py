from courses.models import Course
from django.db import models


class CourseCopy(models.Model):
    course_copy_id = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        verbose_name="ID курса копии",
        help_text="ID курса копии",
    )
    course_id = models.IntegerField(
        verbose_name="ID курса оригинала",
        help_text="ID курса оригинала",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Копия: {self.course_copy_id} Оригинал: {self.course_id}"
