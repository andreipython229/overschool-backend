from django.db import models
from common_services.mixins import AuthorMixin
from schools.models import School


def get_default_students_table_info():
    return [
        {"id": 1, "order": 1, "name": "Имя", "checked": True},
        {"id": 2, "order": 2, "name": "Email", "checked": True},
        {"id": 3, "order": 3, "name": "Суммарный балл", "checked": False},
        {"id": 4, "order": 4, "name": "Курс", "checked": False},
        {"id": 5, "order": 5, "name": "Дата регистрации", "checked": False},
        {"id": 6, "order": 6, "name": "Группа", "checked": False},
        {"id": 7, "order": 7, "name": "Средний балл", "checked": False},
        {"id": 8, "order": 8, "name": "Дата добавления в группу", "checked": False},
        {"id": 9, "order": 9, "name": "Дата удаления из группы", "checked": False},
        {"id": 10, "order": 10, "name": "Прогресс", "checked": False},
    ]


class StudentsTableInfo(AuthorMixin, models.Model):
    """
    Модель для хранения настроек отображения информации о студентах в таблице у админа
    """

    class TableTypes(models.TextChoices):
        SCHOOL = "School", "School"
        COURSE = "Course", "Course"
        GROUP = "Group", "Group"

    students_table_info_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID отображения информации о студентах",
        help_text="Уникальный идентификатор отображения информации о студентах",
    )
    type = models.CharField(
        max_length=10,
        choices=TableTypes.choices,
        verbose_name="Тип отображения таблицы",
        help_text="Может быть: School, Course, Group",
    )
    students_table_info = models.JSONField(
        default=get_default_students_table_info,
        verbose_name="Отображение информации о студентах",
        help_text="Отображение информации о студентах",
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="tables",
        verbose_name="Школа",
        help_text="К какой школе относятся таблицы",
    )

    class Meta:
        verbose_name = "Отображение информации о студентах"
        verbose_name_plural = "Отображение информации о студентах"
