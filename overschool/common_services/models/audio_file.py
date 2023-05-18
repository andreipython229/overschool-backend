from django.db import models
from oauthlib.common import urldecode

from .base_lesson_file import BaseLessonFile


class AudioFile(BaseLessonFile):
    file = models.FileField(
        upload_to="files/audio",
        verbose_name="Ресурс",
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
