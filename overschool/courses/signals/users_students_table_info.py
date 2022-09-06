from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from users.models import User
from courses.models import StudentsTableInfo


@receiver(post_save, sender=User)
def create_students_table_info(sender, instance, created, **kwargs):
    if created: #TODO: сохранять только если админ или кто там надо
        StudentsTableInfo.objects.create(admin=instance)