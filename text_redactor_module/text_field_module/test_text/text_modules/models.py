from django.db import models
from ckeditor.fields import RichTextField


class MainCourseModel(models.Model):
    name = models.CharField(max_length=256, verbose_name="Название курса")
    course_text = RichTextField()



    def __str__(self):
        return str(self.pk)

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"