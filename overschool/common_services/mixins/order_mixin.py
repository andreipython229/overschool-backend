from django.contrib.auth.models import User
from django.db import models


class OrderMixin(models.Model):
    order = models.IntegerField(verbose_name="Порядок")

    class Meta:
        ordering = ["order"]
        abstract = True
