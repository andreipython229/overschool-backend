from courses.models import UserProgressLogs, UserTest
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=UserTest)
def complete_test(sender, instance, **kwargs):
    if instance.success_percent >= instance.test.success_percent:
        progress_log, created = UserProgressLogs.objects.get_or_create(
            user=instance.user, lesson=instance.test
        )
        progress_log.completed = True
        progress_log.save()
