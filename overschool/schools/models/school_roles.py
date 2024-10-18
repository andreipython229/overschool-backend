from django.db import models
from users.models.user import User

from . import School


class SchoolNewRole(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        verbose_name="Школа, в которой выдается доступ на новую роль",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь, которому выдается доступ на новую роль",
    )
    role_name = models.CharField(
        max_length=15,
        blank=False,
        null=False,
        verbose_name="Название новой роли для пользователя (Админ, Учитель, Студент)",
    )

    def __str__(self):
        return f"{self.user} (роль: {self.role_name} в школе {self.school.name})"

    class Meta:
        verbose_name = "Новая роль пользователя"
        verbose_name_plural = "Новые роли пользователей"
        indexes = [
            models.Index(fields=["school"]),
            models.Index(fields=["user"]),
            models.Index(fields=["role_name"]),
        ]
