from django.db import models

class VisibilityMixin(models.Model):
    """
    Миксин для дополнения полем is_visible
    """

    is_visible = models.BooleanField(
        verbose_name="Отображение блока",
        help_text="Видимость в лендинге курса",
        default=True,
    )

    class Meta:
        abstract = True

class PositionMixin(models.Model):
    """
    Миксин для дополнения полями position, can_up и can_down
    """

    position = models.IntegerField(
        verbose_name="Позиция в порядке следования блоков",
        help_text="Номер следования в столбце блоков",
    )
    can_up = models.BooleanField(
        verbose_name="Можно сместить блок вверх",
        help_text="Упирается ли блок в верхний край списка",
    )
    can_down = models.BooleanField(
        verbose_name="Можно сместить блок вниз",
        help_text="Упирается ли блок в нижний край списка",
    )

    class Meta:
        abstract = True
