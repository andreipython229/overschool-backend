from django.db import models

from .user import User


class UtmLabel(models.Model):
    """Модель utm-меток при регистрации пользователя"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="utm_labels_as_user"
    )
    utm_source = models.CharField(
        verbose_name="Источник трафика",
        max_length=150,
        null=True,
        blank=True,
    )
    utm_medium = models.CharField(
        verbose_name="Тип трафика",
        max_length=150,
        null=True,
        blank=True,
    )
    utm_campaign = models.CharField(
        verbose_name="Кампания",
        max_length=150,
        null=True,
        blank=True,
    )
    utm_content = models.CharField(
        verbose_name="Контент ссылки",
        max_length=150,
        null=True,
        blank=True,
    )
    utm_term = models.EmailField(
        verbose_name="Идентификатор элемента рекламного объявления",
        max_length=150,
        null=True,
        blank=True,
    )

    def __str__(self):
        user_info = f"{self.user} - "
        utm_info = ", ".join(
            [
                f"{field.name}: {getattr(self, field.name)}"
                for field in UtmLabel._meta.fields
                if getattr(self, field.name) is not None and field.name != "user"
            ]
        )
        return user_info + utm_info

    class Meta:
        verbose_name = "utm-метка"
        verbose_name_plural = "utm-метки"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["utm_source"]),
            models.Index(fields=["utm_medium"]),
            models.Index(fields=["utm_campaign"]),
            models.Index(fields=["utm_content"]),
            models.Index(fields=["utm_term"]),
        ]
