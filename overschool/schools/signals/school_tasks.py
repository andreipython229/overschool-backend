from datetime import timedelta

from courses.models import Course, Lesson
from courses.models.common.base_lesson import BaseLessonBlock, BlockType
from courses.models.students.students_group import StudentsGroup
from django.conf import settings
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.utils import timezone
from schools.models import Domain, School, SchoolTask, Task
from users.models import UserGroup


@receiver(post_save, sender=School)
def create_initial_tasks(sender, instance, created, **kwargs):
    if created:
        for task_choice in Task.choices:
            SchoolTask.objects.create(school=instance, task=task_choice[0])


def complete_task_and_extend_trial(school, task_name):
    task, created = SchoolTask.objects.get_or_create(school=school, task=task_name)
    if not task.completed:
        task.completed = True
        task.save()
        if school.trial_end_date:
            school.trial_end_date += timedelta(days=1)
        else:
            school.trial_end_date = timezone.now() + timedelta(days=1)

        school.save()


@receiver(post_save, sender=Course)
def mark_create_course_complete(sender, instance, created, **kwargs):
    if (
        created
        and not SchoolTask.objects.filter(
            school=instance.school, task=Task.CREATE_COURSE, completed=True
        ).exists()
    ):
        complete_task_and_extend_trial(instance.school, Task.CREATE_COURSE)


@receiver(post_save, sender=Lesson)
def mark_create_first_lesson_complete(sender, instance, created, **kwargs):
    if (
        created
        and not SchoolTask.objects.filter(
            school=instance.section.course.school,
            task=Task.CREATE_FIRST_LESSON,
            completed=True,
        ).exists()
    ):
        complete_task_and_extend_trial(
            instance.section.course.school, Task.CREATE_FIRST_LESSON
        )


@receiver(post_save, sender=BaseLessonBlock)
def mark_upload_video_complete(sender, instance, created, **kwargs):
    if instance.type == BlockType.VIDEO and instance.video:
        school = instance.base_lesson.section.course.school
        if not SchoolTask.objects.filter(
            school=school, task=Task.UPLOAD_VIDEO, completed=True
        ).exists():
            complete_task_and_extend_trial(school, Task.UPLOAD_VIDEO)


@receiver(post_save, sender=Course)
def mark_publish_course_complete(sender, instance, **kwargs):
    if (
        instance.is_catalog
        and not SchoolTask.objects.filter(
            school=instance.school, task=Task.PUBLISH_COURSE, completed=True
        ).exists()
    ):
        complete_task_and_extend_trial(instance.school, Task.PUBLISH_COURSE)


@receiver(post_save, sender=UserGroup)
def mark_add_first_staff_complete(sender, instance, created, **kwargs):
    if created and instance.group.name == "Teacher":
        school = instance.school
        if not SchoolTask.objects.filter(
            school=school, task=Task.ADD_FIRST_STAFF, completed=True
        ).exists():
            complete_task_and_extend_trial(school, Task.ADD_FIRST_STAFF)


@receiver(post_save, sender=StudentsGroup)
def mark_create_first_group_complete(sender, instance, created, **kwargs):
    if (
        created
        and not SchoolTask.objects.filter(
            school=instance.course_id.school,
            task=Task.CREATE_FIRST_GROUP,
            completed=True,
        ).exists()
    ):
        complete_task_and_extend_trial(
            instance.course_id.school, Task.CREATE_FIRST_GROUP
        )


@receiver(m2m_changed, sender=StudentsGroup.students.through)
def mark_add_first_student_complete(sender, instance, action, **kwargs):
    if action == "post_add":
        group = instance.students_group_fk.first()
        school = group.course_id.school
        if not SchoolTask.objects.filter(
            school=school, task=Task.ADD_FIRST_STUDENT, completed=True
        ).exists():
            complete_task_and_extend_trial(school, Task.ADD_FIRST_STUDENT)


@receiver(post_save, sender=Domain)
def update_allowed_hosts_and_cors(sender, instance, **kwargs):
    if not settings.DEBUG:
        # Базовые хосты
        base_hosts = [
            "platform.coursehb.ru",
            "dev.coursehb.ru",
            "www.coursehb.ru",
            "coursehb.ru",
            "178.159.43.93",
            "178.159.43.93:3000",
        ]

        # Базовые CORS origins
        base_cors_origins = [
            "https://platform.coursehb.ru",
            "https://dev.coursehb.ru",
            "https://www.coursehb.ru",
            "https://coursehb.ru",
        ]

        domains = Domain.objects.filter(nginx_configured=True)

        # Обновляем ALLOWED_HOSTS
        custom_domains = [domain.domain_name for domain in domains]
        settings.ALLOWED_HOSTS = base_hosts + custom_domains

        # Обновляем CORS_ALLOWED_ORIGINS
        custom_cors_origins = [f"https://{domain.domain_name}" for domain in domains]
        settings.CORS_ALLOWED_ORIGINS = base_cors_origins + custom_cors_origins
