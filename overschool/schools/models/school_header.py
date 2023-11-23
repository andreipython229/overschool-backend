from urllib.parse import unquote, urlparse

from ckeditor.fields import RichTextField
from common_services.mixins import TimeStampMixin
from common_services.services import limit_size
from django.db import models
from schools.models import School


class SchoolHeader(TimeStampMixin, models.Model):
    """Модель шапки школы"""

    header_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID школы",
        help_text="Уникальный идентификатор шапки школы",
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Название школы",
        help_text="Главное название школы",
        unique=True,
    )
    description = RichTextField(
        verbose_name="Описание",
        help_text="Описание школы для отображения, сохраняется в html",
        blank=True,
        null=True,
    )
    logo_school = models.ImageField(
        verbose_name="Фотография",
        help_text="Фотография заголовка школы",
        max_length=300,
        validators=[limit_size],
        blank=True,
        null=True,
    )
    photo_background = models.ImageField(
        verbose_name="Фотография",
        help_text="Фотография фона",
        max_length=300,
        validators=[limit_size],
        blank=True,
        null=True,
    )
    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
        related_name="header_school",
        verbose_name="ID школы",
        help_text="ID школы,которой принадлежит школа",
    )

    def logo_school_url(self):
        if self.logo_school:
            parsed_url = urlparse(self.logo_school.url)
            decoded_name = unquote(parsed_url.path.split("/")[-1])
            return decoded_name.split("@", 1)[-1]
        return None

    def photo_background_url(self):
        if self.photo_background:
            parsed_url = urlparse(self.photo_background.url)
            decoded_name = unquote(parsed_url.path.split("/")[-1])

            return decoded_name.split("@", 1)[-1]
        return None

    def __str__(self):
        return str(self.school) + " " + str(self.name)

    class Meta:
        verbose_name = "Шапка школы"
        verbose_name_plural = "Шапки школы"
