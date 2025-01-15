from common_services.mixins import TimeStampMixin
from common_services.services import TruncateFileName, limit_image_size
from django.db import models


class Feedback(TimeStampMixin, models.Model):
    """Модель отзывов о платформе"""

    name = models.CharField(
        help_text="Имя пользователя",
        verbose_name="Имя пользователя",
        max_length=100,
        default="",
        blank=True,
        null=True,
    )
    surname = models.CharField(
        help_text="Фамилия пользователя",
        verbose_name="Фамилия пользователя",
        max_length=100,
        default="",
        blank=True,
        null=True,
    )
    position = models.CharField(
        help_text="Должность пользователя",
        verbose_name="Должность пользователя",
        max_length=500,
        default="",
        blank=True,
        null=True,
    )
    content = models.TextField(
        help_text="Текст отзыва",
        verbose_name="Текст отзыва",
        default="",
        blank=True,
        null=True,
    )
    avatar = models.ImageField(
        help_text="Аватар",
        verbose_name="Аватар",
        max_length=300,
        validators=[limit_image_size],
        upload_to=TruncateFileName(300),
        blank=True,
        null=True,
    )
    rating = models.IntegerField(
        help_text="Рейтинг от 1 до 5",
        verbose_name="Рейтинг от 1 до 5",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.name + ' ' + self.surname} - {self.rating} - {self.content}"

    class Meta:
        verbose_name = "Отзыв о платформе"
        verbose_name_plural = "Отзывы о платформе"
