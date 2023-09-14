from django.db import models


class OrderMixin(models.Model):
    order = models.IntegerField(verbose_name="Порядок", blank=True)

    def save(self, *args, **kwargs):
        if not self.order:
            max_order = self.__class__.objects.all().aggregate(models.Max("order"))[
                "order__max"
            ]
            order = max_order + 1 if max_order is not None else 1
            self.order = order
        super().save(*args, **kwargs)

    class Meta:
        ordering = [models.F("order").desc(nulls_last=True)]
        abstract = True
