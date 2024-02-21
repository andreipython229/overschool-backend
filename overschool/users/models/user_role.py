from common_services.services import TruncateFileName, limit_size
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


class UserSchoolDocuments(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    stamp = models.FileField(
        help_text="Печать школы",
        verbose_name="Печать школы",
        max_length=300,
        validators=[limit_size],
        upload_to=TruncateFileName(300),
        blank=True,
        null=True,
    )
    signature = models.FileField(
        help_text="Подпись школы",
        verbose_name="Подпись школы",
        max_length=300,
        validators=[limit_size],
        upload_to=TruncateFileName(300),
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.user} - {self.school}"

    class Meta:
        verbose_name = "Документы школы"
        verbose_name_plural = "Документы школ"
        unique_together = (("user", "school"),)
