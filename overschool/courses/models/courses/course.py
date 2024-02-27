from ckeditor.fields import RichTextField
from common_services.mixins import AuthorMixin, OrderMixin, TimeStampMixin
from common_services.services import TruncateFileName, limit_size
from django.contrib.postgres.search import SearchVectorField
from django.core.exceptions import ValidationError
from django.db import models
from model_clone import CloneMixin
from oauthlib.common import urldecode
from phonenumber_field.modelfields import PhoneNumberField
from phonenumbers import is_possible_number, is_valid_number, parse
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
    is_catalog = models.BooleanField(
        verbose_name="Видимость в каталоге курсов",
        help_text="Видимость в каталоге курсов",
        default=False,
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
        validators=[limit_size],
        max_length=300,
        upload_to=TruncateFileName(300),
        blank=True,
        null=True,
    )
    search_vector = SearchVectorField(null=True, editable=False)
    _clone_m2o_or_o2m_fields = ["sections"]

    def photo_url(self):
        if self.photo:
            url = urldecode(self.photo.url)
            return url[0][0]
        return None

    def __str__(self):
        return str(self.course_id) + " " + str(self.name)

    class Meta:
        indexes = [models.Index(fields=["search_vector"])]
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        constraints = [
            models.UniqueConstraint(
                fields=["school", "order"], name="unique_school_course_order"
            ),
        ]


class CourseAppeals(TimeStampMixin, models.Model):
    """Модель заявки на курс"""

    id = models.AutoField(
        primary_key=True,
        editable=False,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name="ID курса",
        help_text="ID курса",
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Имя",
        help_text="Имя",
    )
    email = models.EmailField(
        verbose_name="E-mail пользователя",
        help_text="E-mail пользователя",
    )
    phone = PhoneNumberField(
        verbose_name="Телефон пользователя",
        help_text="Телефон пользователя",
    )
    message = models.TextField(
        null=True,
        blank=True,
        verbose_name="Сообщение",
        help_text="Сообщение",
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name="Прочитано",
        help_text="Прочитано",
    )

    def __str__(self):
        return str(self.name) + " " + str(self.email) + " " + str(self.phone)

    def save(self, *args, **kwargs):
        # Получаем номер телефона из self.phone
        phone_number = parse(str(self.phone), None)

        # Проверяем, является ли номер действительным
        if is_valid_number(phone_number) and is_possible_number(phone_number):
            self.phone = phone_number
            super().save(*args, **kwargs)
        else:
            raise ValidationError("Неверный формат номера телефона!")

    class Meta:
        verbose_name = "Заявка на курс"
        verbose_name_plural = "Заявки на курс"
