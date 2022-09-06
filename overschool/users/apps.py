from django.apps import AppConfig
from django.db.models.signals import post_save


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    verbose_name = "Пользователи"

    def ready(self):
        from users.models import User
        from users.signals import create_profile, save_profile
        from courses.signals import create_students_table_info

        post_save.connect(create_profile, sender=User)
        post_save.connect(save_profile, sender=User)
        post_save.connect(create_students_table_info, sender=User)