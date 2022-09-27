from common_services.mixins import OrderMixin
from common_services.models import AuthorPublishedModel, TimeStampedModel
from courses.managers import LessonManager
from django.db import models
from embed_video.fields import EmbedVideoField

from .section import Section
from model_clone import CloneMixin
from ckeditor.fields import RichTextField


## TODO: как загружать бесконечное количество медиа в урок или тест, или дз
class Lesson(TimeStampedModel, AuthorPublishedModel, OrderMixin, CloneMixin):
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
    name = models.CharField(
        max_length=256,
        verbose_name="Название урока",
        help_text="Название урока",
        default="",
    )
    description = models.TextField(
        verbose_name="Описание",
        help_text="Описание к уроку",
        default="",
    )
    video = EmbedVideoField(
        verbose_name="Видео",
        help_text="Сюда всталвяем ссылку на видос с ютуба, поэтому сначала его надо загрузить туда",
        blank=True,
        null=True,
    )
    code = RichTextField(
        verbose_name="Код",
        help_text="Код для урока",
        blank=True,
        null=True,
    )
    file = models.FileField(
        upload_to="pdf/lesson/main",
        verbose_name="Файл урока",
        help_text="Загрузить методичку для урока",
        blank=True,
        null=True,
    )
    audio = models.FileField(
        upload_to="audio/lesson/main",
        verbose_name="Аудиофайл",
        help_text="Загрузить аудио ......",
        blank=True,
        null=True,
    )
    balls = models.PositiveIntegerField(verbose_name="Кол-во баллов за урок",
                                        help_text="Кол-во баллов за урок")

    _clone_m2o_or_o2m_fields = ["homeworks", "lessons"]

    objects = LessonManager()

    def file_url(self):
        if self.file:
            return "https://api.itdev.by" + self.file.url
        return None

    def audio_url(self):
        if self.audio:
            return "https://api.itdev.by" + self.audio.url
        return None

    def __str__(self):
        return str(self.lesson_id) + " " + str(self.name)

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
