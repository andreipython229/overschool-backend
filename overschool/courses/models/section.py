from common_services.mixins import OrderMixin
from common_services.models import AuthorPublishedModel, TimeStampedModel
from courses.managers import SectionManager
from django.db import models

from .course import Course
from model_clone import CloneMixin


class Section(TimeStampedModel, AuthorPublishedModel, OrderMixin, CloneMixin):
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
    _clone_m2o_or_o2m_fields = ["lessons", "homeworks", "tests"]

    objects = SectionManager()

    def __str__(self):
        return str(self.section_id) + " " + str(self.name)

    class Meta:
        verbose_name = "Раздел"
        verbose_name_plural = "Разделы"
