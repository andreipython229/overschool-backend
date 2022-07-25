from common_services.models import TimeStampedModel
from django.db import models


class AudioFile(TimeStampedModel):
    description = models.TextField(
        verbose_name="Описание", help_text="Описание к аудио", null=True, blank=True
    )
    file = models.FileField(
        upload_to="media/courses/audio/files",
        verbose_name="Аудиофайл",
    )

    class Meta:
        verbose_name = "Аудиофайл"
        verbose_name_plural = "Аудиофайлы"
