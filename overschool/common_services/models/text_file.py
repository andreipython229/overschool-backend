from common_services.services import limit_size
from django.db import models
from oauthlib.common import urldecode

from .base_lesson_file import BaseLessonFile


class TextFile(BaseLessonFile):
    file = models.FileField(verbose_name="Ресурс", validators=[limit_size])

    def file_url(self):
        if self.file:
            url = urldecode(self.file.url)
            return url[0][0]
        return None

    class Meta:
        verbose_name = "Текстовый файл"
        verbose_name_plural = "Текстовые файлы"
        default_related_name = "text_files"
        constraints = [
            models.UniqueConstraint(
                fields=["base_lesson", "user_homework", "user_homework_check", "order"],
                name="unique_text_file_order",
            ),
        ]
