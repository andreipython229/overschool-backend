from django.db.models.signals import post_save
from django.dispatch import receiver

from courses.models import UserProgressLogs, UserTest


@receiver(post_save, sender=UserTest)
def complete_test(sender, instance, **kwargs):
    if instance.success_percent >= instance.test.success_percent:
        UserProgressLogs.objects.bulk_create(
            [UserProgressLogs(user=instance.user, lesson=instance.test)]
        )
