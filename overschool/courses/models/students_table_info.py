from django.db import models

from users.models import User


def get_default_students_table_info():
    return [
        {"id": 1, "order": 1, "name": "Имя", "checked": True},
        {"id": 2, "order": 2, "name": "Email", "checked": True},
        {"id": 3, "order": 3, "name": "Суммарный балл", "checked": False},
        {"id": 4, "order": 4, "name": "Курс", "checked": False},
        {"id": 5, "order": 5, "name": "Последняя активность", "checked": False},
        {"id": 6, "order": 6, "name": "Прогресс", "checked": False},
        {"id": 7, "order": 7, "name": "Комментарий", "checked": True},
        {"id": 8, "order": 8, "name": "Группа", "checked": False},
        {"id": 9, "order": 9, "name": "Средний балл", "checked": False},
        {"id": 10, "order": 10, "name": "Дата обновления", "checked": False},
        {"id": 11, "order": 11, "name": "Дата заверения", "checked": False},
    ]


class StudentsTableInfo(models.Model):
    """
    Модель для хранения настроек отображения информации о студентах в таблице у админа
    """

    students_table_info_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID отображения информации о студентах",
        help_text="Уникальный идентификатор отображения информации о студентах",
    )
    admin = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        default=1,
        verbose_name="Админ",
        help_text="Пользователь, являющийся админом, по умолчанию - супер админ",
    )
    students_table_info = models.JSONField(
        default=get_default_students_table_info,
        verbose_name="Отображение информации о студентах",
        help_text="Отображение информации о студентах",
    )

    class Meta:
        verbose_name = "Отображение информации о студентах"
        verbose_name_plural = "Отображение информации о студентах"
