from django.db import models
from schools.models.school import School
from users.models.user import User


class SchoolUser(models.Model):
    """Модель связующая модели юзера и школы к которой он пренадлежит"""

    school_user_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID модели юзера и школы",
        help_text="Уникальный идентификатор связуещей модели юзера и школы",
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="school_user",
        verbose_name="ID школы",
        help_text="ID школы, к которой пренадлежит юзер",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_school",
        verbose_name="ID юзера",
        help_text="ID юзера школы",
    )

    def __str__(self):
        return str(self.user) + " " + str(self.school)

    class Meta:
        verbose_name = "Связующая модель юзера и школы"
        verbose_name_plural = "Связующие модели юзера и школы"
