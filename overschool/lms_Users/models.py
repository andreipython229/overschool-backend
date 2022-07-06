from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, Permission, PermissionsMixin
from django.db import models
import pgtrigger


class Roles(models.Model):
    role = models.CharField(max_length=20, blank=False)
    user_permissions = models.ManyToManyField(Permission)

    def __str__(self):
        return self.role


class MyUserManager(BaseUserManager):

    def _create_user(self, email, username, password, **extra_fields):
        if not email:
            raise ValueError("Вы не ввели Email")
        if not username:
            raise ValueError("Вы не ввели Логин")
        user = self.model(
            email=self.normalize_email(email),
            username=username,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, username, password):
        return self._create_user(email, username, password)

    def create_superuser(self, email, username, password):
        role = Roles.objects.get(id=5)
        return self._create_user(email, username, password, is_staff=True, is_superuser=True, role=role)


# @pgtrigger.register(
#     pgtrigger.Protect(
#         name='set_user_permissions',
#         operation=pgtrigger.Insert | pgtrigger.Update,
#         when=pgtrigger.Before,
#         func=f"UPDATE user SET user_permissions = '{Roles.objects.get()}' WHERE role = '';",
#     )
# )
class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    role = models.ForeignKey(Roles, on_delete=models.CASCADE)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = MyUserManager()

    def __str__(self):
        return self.username
