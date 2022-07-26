from django.contrib.auth.models import Group


class UserRole(Group):
    class Meta:
        proxy = True
        verbose_name = "Роль"
        verbose_name_plural = "Роли"
