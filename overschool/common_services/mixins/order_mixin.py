from django.db import models


def generate_order(model):
    # Ваша логика для определения порядка
    # Например, получение максимального порядка из базы данных для данной модели и увеличение его на 1
    max_order = model.objects.all().aggregate(models.Max('order'))['order__max']
    if max_order is not None:
        return max_order + 1
    else:
        return 1


class OrderMixin(models.Model):
    order = models.IntegerField(verbose_name="Порядок", default=generate_order)

    class Meta:
        ordering = [models.F("order").desc(nulls_last=True)]
        abstract = True
