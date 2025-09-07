from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class Tariff(models.Model):
    """
    Модель тарифного плана
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Название тарифа"),
        help_text=_("Уникальное название тарифного плана")
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Стоимость"),
        help_text=_("Цена тарифа в рублях")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активен"),
        help_text=_("Доступен ли тариф для выбора")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Подробное описание тарифного плана")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата создания")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Дата обновления")
    )

    def clean(self):
        """Валидация данных модели"""
        if self.price < 0:
            raise ValidationError(_("Цена тарифа не может быть отрицательной"))

    def save(self, *args, **kwargs):
        """Переопределение сохранения с валидацией"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.price} руб.)"

    class Meta:
        verbose_name = _("Тариф")
        verbose_name_plural = _("Тарифы")
        ordering = ['price']
        indexes = [
            models.Index(fields=['name'], name='tariff_name_idx'),
            models.Index(fields=['is_active'], name='tariff_active_idx'),
        ]