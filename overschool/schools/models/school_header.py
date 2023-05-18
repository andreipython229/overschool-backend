from ckeditor.fields import RichTextField
from django.db import models
from oauthlib.common import urldecode

from common_services.mixins import TimeStampMixin


class SchoolHeader(TimeStampMixin, models.Model):
    """Модель шапки курсов"""

    school_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID школы",
        help_text="Уникальный идентификатор школы",
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
        upload_to="images/school/main/",
        verbose_name="Фотография",
        help_text="Фотография заголовка школы",
        blank=True,
        null=True,
    )
    logo_header = models.ImageField(
        upload_to="images/school/main/",
        verbose_name="Фотография",
        help_text="Фотография заголовка",
        blank=True,
        null=True,
    )
    photo_background = models.ImageField(
        upload_to="images/school/main/",
        verbose_name="Фотография",
        help_text="Фотография фона",
        blank=True,
        null=True,
    )
    favicon = models.ImageField(
        upload_to="images/school/main/",
        verbose_name="Фотография",
        help_text="Значок веб-сайта",
        blank=True,
        null=True,
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
        return str(self.school_id) + " " + str(self.name)

    class Meta:
        verbose_name = "Шапка школы"
        verbose_name_plural = "Шапки школы"
