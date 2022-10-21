from ckeditor.fields import RichTextField
from django.db import models
from embed_video.fields import EmbedVideoField

from common_services.mixins import AuthorMixin, OrderMixin, TimeStampMixin

from .section import Section


class BaseLesson(TimeStampMixin, AuthorMixin, OrderMixin, models.Model):
    """Базовая модель урока в разделе"""

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
    name = models.CharField(
        max_length=256,
        verbose_name="Название урока",
        help_text="Название урока",
        default="Имя не придумано",
    )
    description = RichTextField(
        verbose_name="Описание", help_text="Описание к уроку", blank=True, null=True
    )
    video = EmbedVideoField(
        verbose_name="Видео",
        help_text="Сюда всталвяем ссылку на видос с ютуба, поэтому сначала его надо загрузить туда",
        blank=True,
        null=True,
    )
    points = models.PositiveIntegerField(
        verbose_name="Баллы за прохождение",
        help_text="Баллы за прохождение",
        default=0,
    )

    def __str__(self):
        return f"{self.lesson_id}. {self.name}"
