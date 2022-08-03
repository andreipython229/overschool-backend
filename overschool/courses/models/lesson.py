from common_services.mixins import OrderMixin
from common_services.models import AuthorPublishedModel, TimeStampedModel
from courses.managers import LessonManager
from django.db import models
from embed_video.fields import EmbedVideoField

from .section import Section


class Lesson(TimeStampedModel, AuthorPublishedModel, OrderMixin):
    """Модель урока в разделе"""

    lesson_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID Урока",
        help_text="Уникальный идентификатор урока",
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="ID раздела",
        help_text="ID раздела курса",
    )
    name = models.CharField(max_length=256, verbose_name="Название урока", help_text="Название урока")
    description = models.TextField(verbose_name="Описание", help_text="Описание к уроку")
    video = EmbedVideoField(
        verbose_name="Видео",
        help_text="Сюда всталвяем ссылку на видос с ютуба, поэтому сначала его надо загрузить туда",
    )

    objects = LessonManager()

    def __str__(self):
        return str(self.lesson_id) + " " + str(self.name)

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
