from django.apps import AppConfig


class CoursesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "courses"

    def ready(self):
        from django.db.models.signals import post_save

        from courses.models import UserHomework, UserTest
        from courses.signals import complete_homework, complete_test

        post_save.connect(complete_homework, sender=UserHomework)
        post_save.connect(complete_test, sender=UserTest)
