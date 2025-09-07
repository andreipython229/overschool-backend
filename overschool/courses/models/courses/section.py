from common_services.mixins import AuthorMixin, OrderMixin, TimeStampMixin
from django.db import models, transaction
from schools.models.core import CloneMixin

from .course import Course


class Section(TimeStampMixin, AuthorMixin, OrderMixin, CloneMixin, models.Model):
    """Модель раздела курса"""

    section_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID Раздела",
        help_text="Уникальный идентификатор раздела",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name="ID курса",
        help_text="ID курса раздела",
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Название курса",
        help_text="Название раздела курса",
    )
    _clone_m2o_or_o2m_fields = ["lessons"]

    def __str__(self):
        return str(self.section_id) + " " + str(self.name)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if not self.order:
                max_order = Section.objects.filter(course=self.course).aggregate(models.Max("order"))["order__max"]
                self.order = max_order + 1 if max_order is not None else 1
            else:
                Section.objects.filter(course=self.course, order__gte=self.order).update(order=models.F("order") + 1)

            super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Раздел"
        verbose_name_plural = "Разделы"
        indexes = [
            models.Index(fields=["course"]),
            models.Index(fields=["name"]),
        ]
