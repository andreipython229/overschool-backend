from django.apps import AppConfig
from django.db.models.signals import post_save


class LessonTestsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "lesson_tests"

    def ready(self):
        from lesson_tests.models import UserTest
        from lesson_tests.signals import save_progress

        post_save.connect(save_progress, sender=UserTest)
