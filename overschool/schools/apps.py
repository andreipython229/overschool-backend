from django.apps import AppConfig


class SchoolsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "schools"

    def ready(self):
        from courses.models import Course, Lesson
        from courses.models.common.base_lesson import BaseLessonBlock, BlockType
        from courses.models.students.students_group import StudentsGroup
        from django.conf import settings
        from django.db.models.signals import post_save
        from schools.models import Domain, School
        from schools.signals import (
            create_initial_tasks,
            mark_add_first_staff_complete,
            mark_add_first_student_complete,
            mark_create_course_complete,
            mark_create_first_group_complete,
            mark_create_first_lesson_complete,
            mark_publish_course_complete,
            mark_upload_video_complete,
            update_allowed_hosts_and_cors,
        )
        from users.models import UserGroup

        if not settings.DEBUG:
            try:
                domains = Domain.objects.filter(nginx_configured=True)
                # Обновляем ALLOWED_HOSTS
                custom_domains = [domain.domain_name for domain in domains]
                if custom_domains:
                    settings.ALLOWED_HOSTS.extend(custom_domains)
                # Обновляем CORS_ALLOWED_ORIGINS
                custom_cors_origins = [
                    f"https://{domain.domain_name}" for domain in domains
                ]
                if custom_cors_origins:
                    settings.CORS_ALLOWED_ORIGINS.extend(custom_cors_origins)
            except Exception as e:
                print(f"Error updating hosts and origins: {e}")

        post_save.connect(create_initial_tasks, sender=School)

        post_save.connect(
            mark_add_first_student_complete, sender=StudentsGroup.students.through
        )

        post_save.connect(mark_add_first_staff_complete, sender=UserGroup)

        post_save.connect(mark_create_course_complete, sender=Course)

        post_save.connect(mark_create_first_group_complete, sender=StudentsGroup)

        post_save.connect(mark_create_first_lesson_complete, sender=Lesson)

        post_save.connect(mark_publish_course_complete, sender=Course)

        post_save.connect(mark_upload_video_complete, sender=BaseLessonBlock)

        post_save.connect(update_allowed_hosts_and_cors, sender=Domain)
