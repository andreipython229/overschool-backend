from django.core.validators import FileExtensionValidator
from django.db import models

from .base_lesson_file import BaseLessonFile


class TextFile(BaseLessonFile):
    file = models.FileField(
        upload_to="files/text",
        verbose_name="Ресурс",
    )

    class Meta:
        verbose_name = "Текстовый файл"
        verbose_name_plural = "Текстовые файлы"
        default_related_name = "text_files"

