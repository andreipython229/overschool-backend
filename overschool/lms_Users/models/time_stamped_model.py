from django.db import models


class TimeStampedModel(models.Model):
    """
    Базовая модель для дополнения остальных полями created_at и updated_at
    """

    created_on = models.DateTimeField(auto_now_add=True, verbose_name="Создано",
                                      help_text="Дата и время, когда запись была создана")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено",
                                      help_text="Дата, когда запись была последний раз обновлена")

    class Meta:
        abstract = True
