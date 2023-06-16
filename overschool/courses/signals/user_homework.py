from django.db.models.signals import post_save
from django.dispatch import receiver

from courses.models import UserHomework, UserProgressLogs


@receiver(post_save, sender=UserHomework)
def complete_homework(sender, instance, **kwargs):
    if instance.status == "ПРА":
        # UserProgressLogs.objects.bulk_create(
        #     [UserProgressLogs(user=instance.user, lesson=instance.homework)]
        # )
        progress_log, created = UserProgressLogs.objects.get_or_create(user=instance.user, lesson=instance.homework)
        progress_log.completed = True
        progress_log.save()

