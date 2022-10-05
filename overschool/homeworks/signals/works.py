from courses.models import UserProgressLogs
from django.db.models.signals import post_save
from django.dispatch import receiver
from homeworks.models import UserHomework


@receiver(post_save, sender=UserHomework)
def save_progress(sender, instance, **kwargs):
    if instance.status == "ПРА":
        UserProgressLogs.objects.bulk_create([UserProgressLogs(user=instance.user, homework=instance.homework)])
