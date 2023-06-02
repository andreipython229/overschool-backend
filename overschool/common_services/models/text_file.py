from django.db import models
from oauthlib.common import urldecode

from .base_lesson_file import BaseLessonFile


class TextFile(BaseLessonFile):
    file = models.FileField(
        verbose_name="Ресурс",
    )

    def file_url(self):
        if self.file:
            url = urldecode(self.file.url)
            return url[0][0]
        return None

    class Meta:
        verbose_name = "Текстовый файл"
        verbose_name_plural = "Текстовые файлы"
        default_related_name = "text_files"
