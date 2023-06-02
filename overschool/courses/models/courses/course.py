from ckeditor.fields import RichTextField
from common_services.mixins import AuthorMixin, OrderMixin, TimeStampMixin
from django.db import models
from model_clone import CloneMixin
from oauthlib.common import urldecode
from schools.models import School


class Public(models.TextChoices):
    "Варианты публикации для курса"
    PUBLISHED = "О", "Опубликован"
    NOT_PUBLISHED = "Н", "Не опубликован"
    HIDDEN = "С", "Скрыт настройками курса"


class Format(models.TextChoices):
    "Варианты форматов для курса"
    OFFLINE = "ОФФ", "Оффлайн"
    ONLINE = "ОН", "Онлайн"


class Course(TimeStampMixin, AuthorMixin, OrderMixin, CloneMixin, models.Model):
    """Модель курсов"""

    course_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="Курс ID",
        help_text="Уникальный идентификатор курса",
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="course_school",
        verbose_name="ID школы",
        help_text="ID школы",
    )
    public = models.CharField(
        max_length=256,
        choices=Public.choices,
        default=Public.NOT_PUBLISHED,
        verbose_name="Формат публикации курса",
        help_text="Формат публикации курса, отображает статус (Опубликован, Не опубликован, Скрыт настройками курса)",
        blank=True,
        null=True,
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Название курса",
        help_text="Главное название курса",
        blank=True,
        null=True,
    )
    format = models.CharField(
        max_length=256,
        choices=Format.choices,
        default=Format.ONLINE,
        verbose_name="Формат курса",
        help_text="Формат курса, отображает формат обучения (Онлайн либо Оффлайн)",
        blank=True,
        null=True,
    )
    duration_days = models.PositiveIntegerField(
        verbose_name="Продолжительность курса",
        help_text="Продолжительность курса в днях",
        blank=True,
        null=True,
    )
    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Цена",
        help_text="Цена курса в BYN",
        blank=True,
        null=True,
    )
    description = RichTextField(
        verbose_name="Описание",
        help_text="Описание курса для отображения, сохраняется в html",
        blank=True,
        null=True,
    )
    photo = models.ImageField(
        verbose_name="Фотография",
        help_text="Главная фотография",
        blank=True,
        null=True,
    )
    _clone_m2o_or_o2m_fields = ["sections"]

    def photo_url(self):
        if self.photo:
            url = urldecode(self.photo.url)
            return url[0][0]
        return None

    def __str__(self):
        return str(self.course_id) + " " + str(self.name)

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
