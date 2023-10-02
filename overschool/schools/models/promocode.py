from django.core.validators import MinValueValidator
from django.db import models


class PromoCode(models.Model):
    name = models.CharField(max_length=255, unique=True)
    discount = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоды"
