from django.apps import AppConfig


class SchoolsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "schools"

    def ready(self):
        from courses.models import Course, Lesson
        from courses.models.common.base_lesson import BaseLessonBlock, BlockType
        from courses.models.students.students_group import StudentsGroup
        from django.db.models.signals import post_save
        from schools.models import School
        from schools.signals import (
            create_initial_tasks,
            mark_add_first_staff_complete,
            mark_add_first_student_complete,
            mark_create_course_complete,
            mark_create_first_group_complete,
            mark_create_first_lesson_complete,
            mark_publish_course_complete,
            mark_upload_video_complete,
        )
        from users.models import UserGroup

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
