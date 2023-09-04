from django.db import models


class OrderMixin(models.Model):
    order = models.AutoField(verbose_name="Порядок")

    class Meta:
        ordering = [models.F("order").desc(nulls_last=True)]
        abstract = True
