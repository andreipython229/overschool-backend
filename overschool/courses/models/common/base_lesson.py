from ckeditor.fields import RichTextField
from common_services.mixins import AuthorMixin, OrderMixin, TimeStampMixin
from django.db import models
from model_clone import CloneMixin

from ..courses.section import Section


class BaseLesson(TimeStampMixin, AuthorMixin, OrderMixin, CloneMixin, models.Model):
    """Базовая модель урока в разделе"""

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
    code = RichTextField(
        verbose_name="Код", help_text="Примеры кода к уроку", blank=True, null=True
    )
    video = models.FileField(
        verbose_name="Видео",
        help_text="Видеофайл размером до 2 ГБ",
        blank=True,
        null=True,
    )
    points = models.PositiveIntegerField(
        verbose_name="Баллы за прохождение",
        help_text="Баллы за прохождение",
        default=0,
    )
    active = models.BooleanField(
        default=False,
        verbose_name="Активный",
        help_text="Определяет, виден ли урок, домашнее задание или тест всем кроме админа",
        blank=False,
    )
    _clone_o2o_fields = ["lessons", "homeworks", "tests"]

    def __str__(self):
        return f"{self.section}. {self.name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["section", "order"], name="unique_section_lesson_order"
            ),
        ]
