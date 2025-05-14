from django.contrib.auth.models import Group
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from schools.models import School
from users.models import User


class UserGroup(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="groups")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="groups")
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="groups")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.group} - {self.school}"

    class Meta:
        verbose_name = "Группа пользователя"
        verbose_name_plural = "Группы пользователей"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["group"]),
            models.Index(fields=["school"]),
        ]


@receiver(post_save, sender=School)
def assign_admin_role(sender, instance, created, **kwargs):
    if created:
        admin_group = Group.objects.get(name="Admin")
        user = User.objects.get(pk=154)
        UserGroup.objects.create(
            user=user,
            group=admin_group,
            school=instance,
        )


class UserRole(Group):
    """Модель роли юзера"""

    class Meta:
        proxy = True
        verbose_name = "Роль"
        verbose_name_plural = "Роли"
