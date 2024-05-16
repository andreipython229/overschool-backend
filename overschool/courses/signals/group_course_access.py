from courses.models.students.students_group import GroupCourseAccess, StudentsGroup
from courses.models.students.user_progress import UserProgressLogs
from courses.services import get_student_progress
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=UserProgressLogs)
def update_group_course_access(sender, instance, **kwargs):
    # Получаем курс и группу пользователя на этом курсе
    course = instance.lesson.section.course
    user_group = instance.user.students_group_fk.filter(course_id=course).first()
    if user_group:
        # Вычисляем процент прогресса пользователя
        progress = get_student_progress(
            instance.user, course.course_id, user_group.group_id
        )
        if progress == 100:
            # Находим все объекты GroupCourseAccess для текущей группы пользователя
            group_course_accesses = GroupCourseAccess.objects.filter(
                current_group=user_group
            )
            for access in group_course_accesses:
                other_groups_on_course = StudentsGroup.objects.filter(
                    course_id=access.course
                )
                user_in_other_group = any(
                    instance.user in group.students.all()
                    for group in other_groups_on_course
                )
                # Если пользователь не состоит больше ни в одной другой группе на этом курсе, добавляем его в текущую группу
                if not user_in_other_group:
                    access.group.students.add(instance.user)
