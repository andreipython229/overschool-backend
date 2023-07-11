from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import UserGroup

from courses.models.students.students_table_info import StudentsTableInfo, get_default_students_table_info


@receiver(post_save, sender=UserGroup)
def create_students_table_info(sender, instance, created, **kwargs):
    if created and instance.user.groups.filter(group__name__in=['Admin', 'Teacher']):
        table_types = StudentsTableInfo.TableTypes.choices
        user = instance.user
        school = instance.school

        for table_type in table_types:
            StudentsTableInfo.objects.create(
                type=table_type[0],
                students_table_info=get_default_students_table_info(),
                author=user,
                school=school
            )
