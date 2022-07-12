from django.db import models

from courses.managers import SectionManager
from overschool.abstract_models import TimeStampedModel

from .course import Course


class Section(TimeStampedModel):
    "Модель раздела курса"
    section_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID Раздела",
        help_text="Уникальный идентификатор раздела",
    )
    course_id = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="course_section_id_fk",
        verbose_name="ID курса",
        help_text="ID курса раздела",
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Название курса",
        help_text="Название раздела курса",
    )
    previous_section_id = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        related_name="section_id_fk",
        verbose_name="ID прошлого раздела",
        help_text="ID предыдущего курса, если ID None - курс первый",
    )

    objects = SectionManager

    def __str__(self):
        return str(self.section_id) + " " + str(self.name)

    def order(self):
        if self.previous_section_id:
            previous_section: Section = Section.objects.get(
                section_id=self.previous_section_id
            )
            return previous_section.order() + 1
        else:
            return 0

    class Meta:
        verbose_name = "Раздел"
        verbose_name_plural = "Разделы"
