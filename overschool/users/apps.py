from django.apps import AppConfig
from django.db.models.signals import post_save


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    verbose_name = "Пользователи"

    def ready(self):
        from users.models import User
        from users.signals import create_users_profile

        post_save.connect(create_users_profile, sender=User)
