from ckeditor.fields import RichTextField
from common_services.mixins import OrderMixin
from common_services.models import AuthorPublishedModel, TimeStampedModel
from courses.managers import CourseManager
from django.db import models


class Format(models.TextChoices):
    "Варианты форматов для курса"
    OFFLINE = "ОФФ", "Оффлайн"
    ONLINE = "ОН", "Онлайн"


class Course(TimeStampedModel, AuthorPublishedModel, OrderMixin):
    """Модель курсов"""

    course_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="Курс ID",
        help_text="Уникальный идентификатор курса",
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Название курса",
        help_text="Главное название курса",
        blank=True,
        null=True
    )
    format = models.CharField(
        max_length=256,
        choices=Format.choices,
        default=Format.ONLINE,
        verbose_name="Формат курса",
        help_text="Формат курса, отображает формат обучения (Онлайн либо Оффлайн)",
        blank=True,
        null=True
    )
    duration_days = models.PositiveIntegerField(
        verbose_name="Продолжительность курса",
        help_text="Продолжительность курса в днях",
        blank=True,
        null=True
    )
    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Цена",
        help_text="Цена курса в BYN",
        blank=True,
        null=True
    )
    description = RichTextField(
        verbose_name="Описание",
        help_text="Описание курса для отображения, сохраняется в html",
        blank=True,
        null=True
    )
    photo = models.ImageField(
        upload_to="images/courses/main/",
        verbose_name="Фотография",
        help_text="Главная фотография",
        blank=True,
        null=True
    )


    objects = CourseManager()

    def photo_url(self):
        if self.photo:
            return "https://api.itdev.by"+self.photo.url
        return None

    def __str__(self):
        return str(self.course_id) + " " + str(self.name)

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
