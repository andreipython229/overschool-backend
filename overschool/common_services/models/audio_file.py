from django.core.validators import FileExtensionValidator
from django.db import models

from .base_lesson_file import BaseLessonFile


class AudioFile(BaseLessonFile):
    file = models.FileField(
        upload_to="files/audio", verbose_name="Ресурс", validators=[FileExtensionValidator(["mp3", "wav", "wma"])]
    )

    class Meta:
        verbose_name = "Аудиофайл"
        verbose_name_plural = "Аудиофайлы"
