from django.contrib.auth.models import Group
from django.db import models
from users.models import User


class UserGroup(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="groups")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="groups")
    school = models.ForeignKey("schools.School", on_delete=models.CASCADE, related_name="groups")
    created_at = models.DateTimeField(auto_now_add=True)

    def str(self):
        return f"{self.user} - {self.group} - {self.school}"

    class Meta:
        verbose_name = "Группа пользователя"
        verbose_name_plural = "Группы пользователей"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["group"]),
            models.Index(fields=["school"]),
        ]


class UserRole(Group):
    """Прокси-модель для ролей пользователя"""

    class Meta:
        proxy = True
        verbose_name = "Роль"
        verbose_name_plural = "Роли"