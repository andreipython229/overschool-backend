from django.contrib.auth.models import Group
from django.db import models
from schools.models import School
from users.models import User


class UserGroup(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="groups")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="groups")
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="groups")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.group} - {self.school}"


class UserRole(Group):
    """Модель роли юзера"""

    class Meta:
        proxy = True
        verbose_name = "Роль"
        verbose_name_plural = "Роли"
