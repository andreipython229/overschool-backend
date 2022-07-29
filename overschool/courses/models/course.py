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
    )
    format = models.CharField(
        max_length=256,
        choices=Format.choices,
        default=Format.ONLINE,
        verbose_name="Формат курса",
        help_text="Формат курса, отображает формат обучения (Онлайн либо Оффлайн)",
    )
    duration_days = models.PositiveIntegerField(
        verbose_name="Продолжительность курса",
        help_text="Продолжительность курса в днях",
    )
    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Цена",
        help_text="Цена курса в BYN",
    )
    description = RichTextField(
        verbose_name="Описание",
        help_text="Описание курса для отображения, сохраняется в html",
    )
    photo = models.ImageField(
        upload_to="images/courses/main/",
        verbose_name="Фотография",
        help_text="Главная фотография",
    )

    objects = CourseManager()

    def __str__(self):
        return str(self.course_id) + " " + str(self.name)

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
