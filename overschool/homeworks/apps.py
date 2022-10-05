from django.apps import AppConfig
from django.db.models.signals import post_save


class HomeworksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "homeworks"

    def ready(self):
        from homeworks.models import UserHomework
        from homeworks.signals import save_progress

        post_save.connect(save_progress, sender=UserHomework)
