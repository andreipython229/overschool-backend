from django.contrib.auth.models import User
from django.db import models


class OrderMixin(models.Model):
    order = models.IntegerField(verbose_name="Порядок", null=True)

    class Meta:
        ordering = [models.F("order").desc(nulls_last=True)]
        abstract = True
