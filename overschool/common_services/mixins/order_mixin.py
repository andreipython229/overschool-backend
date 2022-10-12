from django.db import models


class OrderMixin(object):
    order = models.IntegerField(verbose_name="Порядок")

    class Meta:
        ordering = [models.F("order").desc(nulls_last=True)]
