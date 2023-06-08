from common_services.mixins import OrderMixin
from django.db import models

from .base_lesson import BaseLesson


class ComponentTypeChoices(models.TextChoices):
    """Типы компонентов урока"""

    TEXT = "Текст", "Текст"
    VIDEO = "Видео", "Видео"
    TEXT_FILE = "Текстовый файл", "Текстовый файл"
    AUDIO_FILE = "Аудиофайл", "Аудиофайл"


class LessonComponentsOrder(OrderMixin, models.Model):
    """Модель порядка компонентов внутри урока"""

    base_lesson = models.ForeignKey(
        BaseLesson,
        on_delete=models.CASCADE,
        related_name="all_components",
        verbose_name="ID базового урока",
        help_text="ID базового урока, к которому относится компонент с соответствующим порядком",
    )
    component_type = models.CharField(
        max_length=256,
        choices=ComponentTypeChoices.choices,
        verbose_name="Тип компонента",
        help_text="Тип компонента урока, для которого определен порядок",
    )

    def __str__(self):
        return f"{self.base_lesson}. {self.component_type}"

    class Meta:
        verbose_name = "Компонент урока с определенным номером по порядку"
        verbose_name_plural = "Порядок компонентов внутри урока"
        constraints = [
            models.UniqueConstraint(
                fields=["base_lesson", "order"], name="unique_lesson_component_order"
            ),
        ]
