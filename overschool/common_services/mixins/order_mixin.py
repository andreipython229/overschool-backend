from django.db import models


class OrderMixin:
    order = models.IntegerField(verbose_name="Порядок")

    class Meta:
        ordering = [models.F("order").desc(nulls_last=True)]
