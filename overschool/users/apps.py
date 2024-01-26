from django.apps import AppConfig
from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    verbose_name = "Пользователи"

    def ready(self):
        from users.models import User
        from users.signals import create_profile, save_profile, update_last_login_test

        post_save.connect(create_profile, sender=User)
        post_save.connect(save_profile, sender=User)
        user_logged_in.connect(update_last_login_test)
