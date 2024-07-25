from common_services.services import TruncateFileName, limit_image_size
from courses.models.students.students_group import StudentsGroup
from django.db import models
from schools.models import School


class Bonus(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="bonuses",
        verbose_name="ID школы",
        help_text="ID школы",
    )
    logo = models.ImageField(
        verbose_name="Логотип",
        help_text="Логотип акции",
        validators=[limit_image_size],
        upload_to=TruncateFileName(300),
        max_length=300,
        blank=True,
        null=True,
    )
    text = models.TextField(
        verbose_name="Описание",
        help_text="Описание акции",
        blank=True,
        null=True,
    )
    link = models.URLField(verbose_name="Ссылка на акцию")
    expire_date = models.DateTimeField(
        verbose_name="Дата и время окончания акции",
        help_text="Дата и время окончания акции",
    )
    active = models.BooleanField(
        default=False,
        verbose_name="Активный",
        help_text="Определяет, активирован ли бонус",
        blank=False,
    )
    student_groups = models.ManyToManyField(
        StudentsGroup,
        verbose_name="Группы",
        help_text="Группы, которым предоставлен бонус",
        related_name="group_bonuses",
        blank=True,
    )

    def __str__(self):
        return f"{self.school} - {self.link}"

    class Meta:
        verbose_name = "Бонус"
        verbose_name_plural = "Бонусы"


# class GroupBonus(models.Model):
#     bonus = models.ForeignKey(
#         Bonus,
#         on_delete=models.CASCADE,
#         related_name="group_bonuses",
#         verbose_name="Бонус",
#         help_text="Предоставленный группе бонус",
#     )
#     group = models.ForeignKey(
#         StudentsGroup,
#         on_delete=models.CASCADE,
#         related_name="group_bonuses",
#         verbose_name="Группа",
#         help_text="Группа, которой предоставлен бонус",
#     )
#
#     def __str__(self):
#         return f"{self.bonus} -> {self.group}"
#
#     class Meta:
#         verbose_name = "Бонус для группы"
#         verbose_name_plural = "Бонусы для групп"
