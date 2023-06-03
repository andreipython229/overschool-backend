from common_services.mixins import OrderMixin, TimeStampMixin
from django.db import models
from oauthlib.common import urldecode
from schools.managers import SchoolManager


class School(TimeStampMixin, OrderMixin):
    """Модель школы"""

    school_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID школы",
        help_text="Уникальный идентификатор школы",
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Название",
        help_text="Название школы",
        default="Имя не придумано",
    )
    avatar = models.ImageField(
        verbose_name="Фотография",
        help_text="Фотография школы",
        blank=True,
        null=True,
    )

    objects = SchoolManager()

    def avatar_url(self):
        if self.avatar:
            url = urldecode(self.avatar.url)
            return url[0][0]
        return None

    def __str__(self):
        return str(self.school_id) + " " + str(self.name)

    class Meta:
        verbose_name = "Школа"
        verbose_name_plural = "Школы"
