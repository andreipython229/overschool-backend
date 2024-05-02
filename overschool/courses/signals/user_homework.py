from courses.models import UserHomework, UserProgressLogs
from courses.models.homework.user_homework import UserHomeworkStatusChoices
from courses.models.homework.user_homework_check import UserHomeworkCheck
from django.db.models.signals import post_save
from django.dispatch import receiver

from tg_notifications.views import SendNotifications

@receiver(post_save, sender=UserHomework)
def complete_homework(sender, instance, **kwargs):
    if instance.status == UserHomeworkStatusChoices.SUCCESS:
        progress_log, created = UserProgressLogs.objects.get_or_create(
            user=instance.user, lesson=instance.homework
        )
        progress_log.completed = True
        progress_log.save()


@receiver(post_save, sender=UserHomework)
def create_user_homework_check(sender, instance, created, **kwargs):
    if created:
        user_homework_check = UserHomeworkCheck.objects.create(user_homework=instance)
        user_homework_check.text = instance.text
        user_homework_check.status = instance.status
        user_homework_check.author = instance.user
        user_homework_check.save()


@receiver(post_save, sender=UserHomeworkCheck)
def update_user_homework_status(sender, instance, **kwargs):
    user_homework = instance.user_homework
    last_check_status = (
        UserHomeworkCheck.objects.filter(user_homework=user_homework)
        .order_by("-created_at")
        .values_list("status", flat=True)
        .first()
    )
    last_check_mark = (
        UserHomeworkCheck.objects.filter(user_homework=user_homework)
        .order_by("-created_at")
        .values_list("mark", flat=True)
        .first()
    )
    SendNotifications.last_notifications(
        user_homework,
        last_check_status,
        last_check_mark
    )

    if last_check_status:
        user_homework.status = last_check_status
    if last_check_mark:
        user_homework.mark = last_check_mark
    user_homework.save()
