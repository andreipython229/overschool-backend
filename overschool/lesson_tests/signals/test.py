from courses.models import UserProgressLogs
from django.db.models.signals import post_save
from django.dispatch import receiver
from lesson_tests.models import UserTest


@receiver(post_save, sender=UserTest)
def save_progress(sender, instance, **kwargs):
    if instance.success_percent >= instance.test.success_percent:
        UserProgressLogs.objects.bulk_create([UserProgressLogs(user=instance.user, section_test=instance.test)])
