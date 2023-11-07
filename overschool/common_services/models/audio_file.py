from common_services.services import limit_size
from django.db import models
from oauthlib.common import urldecode

from .base_lesson_file import BaseLessonFile


class AudioFile(BaseLessonFile):
    file = models.FileField(
        verbose_name="Ресурс", max_length=300, validators=[limit_size]
    )

    def file_url(self):
        if self.file:
            url = urldecode(self.file.url)
            return url[0][0]
        return None

    class Meta:
        verbose_name = "Аудиофайл"
        verbose_name_plural = "Аудиофайлы"
        default_related_name = "audio_files"
