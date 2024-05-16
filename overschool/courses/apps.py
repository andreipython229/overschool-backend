from django.apps import AppConfig


class CoursesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "courses"

    def ready(self):
        from courses.models import (
            UserHomework,
            UserHomeworkCheck,
            UserProgressLogs,
            UserTest,
        )
        from courses.signals import (
            complete_homework,
            complete_test,
            create_students_table_info,
            create_user_homework_check,
            update_group_course_access,
            update_user_homework_status,
        )
        from django.db.models.signals import post_save
        from users.models import UserGroup

        post_save.connect(complete_homework, sender=UserHomework)
        post_save.connect(complete_test, sender=UserTest)
        post_save.connect(update_group_course_access, sender=UserProgressLogs)
        post_save.connect(create_user_homework_check, sender=UserHomework)
        post_save.connect(update_user_homework_status, sender=UserHomeworkCheck)
        post_save.connect(create_students_table_info, sender=UserGroup)
