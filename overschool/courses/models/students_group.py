from common_services.models import TimeStampedModel
from django.db import models
from .course import Course
from users.models.user import User


class StudentsGroup(TimeStampedModel):
    """
    Модель группы студентов
    """
    group_id = models.AutoField(
        primary_key=True,
        editable=True,
        verbose_name="Группа ID",
        help_text="Уникальный идентификатор группы",
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Название группы",
        help_text="Название группы",
    )
    course_id = models.ForeignKey(Course,
                                  on_delete=models.PROTECT,
                                  verbose_name="Курс",
                                  help_text="Курс, который проходит эта группа",
                                  related_name="group_course_fk")
    teacher_id = models.ForeignKey(User,
                                   on_delete=models.SET_DEFAULT,
                                   default=1,
                                   verbose_name="Преподаватель",
                                   help_text="Преподаватель, который ведёт эту группу",
                                   related_name="teacher_group_fk")
    students = models.ManyToManyField(User, verbose_name="Ученики",
                                      help_text="Ученики этой группы",
                                      related_name="students_group_fk")

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = "Группа студентов"
        verbose_name_plural = "Группы студентов"

