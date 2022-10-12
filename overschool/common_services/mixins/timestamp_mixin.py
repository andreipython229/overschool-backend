from django.db import models


class TimeStampMixin:
    """
    Миксин для дополнения полями created_at и updated_at
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано",
        help_text="Дата и время, когда запись была создана",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Обновлено",
        help_text="Дата, когда запись была последний раз обновлена",
    )
