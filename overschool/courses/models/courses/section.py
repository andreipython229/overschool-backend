from common_services.mixins import AuthorMixin, OrderMixin, TimeStampMixin
from django.db import models
from model_clone import CloneMixin

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

    class Meta:
        verbose_name = "Раздел"
        verbose_name_plural = "Разделы"
        constraints = [
            models.UniqueConstraint(
                fields=["course", "order"], name="unique_course_section_order"
            ),
        ]
