from ckeditor.fields import RichTextField
from common_services.models import TimeStampedModel
from django.db import models


class CourseHeader(TimeStampedModel):
    """Модель шапки курсов"""

    school_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID школы",
        help_text="Уникальный идентификатор школы",
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Название школы",
        help_text="Главное название школы",
        unique=True,
    )
    description = RichTextField(
        verbose_name="Описание",
        help_text="Описание школы для отображения, сохраняется в html",
    )
    photo_header = models.ImageField(
        upload_to="images/courses/school/",
        verbose_name="Фотография",
        help_text="Фотография заголовка",
    )
    photo_background = models.ImageField(
        upload_to="images/courses/school/",
        verbose_name="Фотография",
        help_text="Фотография фона",
    )

    def __str__(self):
        return str(self.school_id) + " " + str(self.name)

    class Meta:
        verbose_name = "Шапка курсов"
        verbose_name_plural = "Шапки курсов"
