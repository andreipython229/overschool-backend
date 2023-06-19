from ckeditor.fields import RichTextField
from common_services.mixins import TimeStampMixin
from common_services.services import limit_size
from django.db import models
from oauthlib.common import urldecode
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
        blank=True,
        null=True,
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
        validators=[limit_size],
        blank=True,
        null=True,
    )
    logo_header = models.ImageField(
        verbose_name="Фотография",
        help_text="Фотография заголовка",
        validators=[limit_size],
        blank=True,
        null=True,
    )
    photo_background = models.ImageField(
        verbose_name="Фотография",
        help_text="Фотография фона",
        validators=[limit_size],
        blank=True,
        null=True,
    )
    favicon = models.ImageField(
        verbose_name="Фотография",
        help_text="Значок веб-сайта",
        validators=[limit_size],
        blank=True,
        null=True,
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="header_school",
        verbose_name="ID школы",
        help_text="ID школы,которой принадлежит школа",
    )

    def logo_school_url(self):
        if self.logo_school:
            url = urldecode(self.logo_school.url)
            return url[0][0]
        return None

    def logo_header_url(self):
        if self.logo_header:
            url = urldecode(self.logo_header.url)
            return url[0][0]
        return None

    def photo_background_url(self):
        if self.photo_background:
            url = urldecode(self.photo_background.url)
            return url[0][0]
        return None

    def favicon_url(self):
        if self.favicon:
            url = urldecode(self.favicon.url)
            return url[0][0]
        return None

    def __str__(self):
        return str(self.school) + " " + str(self.name)

    class Meta:
        verbose_name = "Шапка школы"
        verbose_name_plural = "Шапки школы"
