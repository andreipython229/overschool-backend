from common_services.models import TimeStampedModel
from django.db import models
from users.models import User


def get_default_students_table_info():
    return {
        'name': {
            'display': True,
            'order': 1
        },
        'email': {
            'display': True,
            'order': 2
        },
        'last_activity': {
            'display': True,
            'order': 3
        },
        'average_mark': {
            'display': True,
            'order': 4
        },
        'sum_mark': {
            'display': True,
            'order': 5
        },
        'updated_at': {
            'display': True,
            'order': 6
        },
        'course': {
            'display': True,
            'order': 7
        },
        'assurance_date': {
            'display': False,
            'order': 8
        },
        'progress': {
            'display': False,
            'order': 9
        },
        'comment': {
            'display': False,
            'order': 10
        },
        'group': {
            'display': False,
            'order': 11
        }
    }

# TODO: показать Виталику JS0N


class StudentsTableInfo(TimeStampedModel):
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
    ) # TODO: сделать так, чтобы про создании админа создавалась модель
    students_table_info = models.JSONField(
        default=get_default_students_table_info,
        verbose_name="Отображение информации о студентах",
        help_text="Отображение информации о студентах",
    )

    class Meta:
        verbose_name = "Отображение информации о студентах"
        verbose_name_plural = "Отображение информации о студентах"
