from common_services.models import AudioFile, TextFile
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=TextFile)
def copy_text_file_to_homework_check(sender, instance, created, **kwargs):
    if instance.user_homework:
        # Создаем соответствующий TextFile в user_homework_check
        user_homework_check = instance.user_homework.user_homework_checks.first()
        if user_homework_check:
            TextFile.objects.create(
                file=instance.file,
                user_homework_check=user_homework_check,
            )


@receiver(post_save, sender=AudioFile)
def copy_audio_file_to_homework_check(sender, instance, created, **kwargs):
    if instance.user_homework:
        # Создаем соответствующий TextFile в user_homework_check
        user_homework_check = instance.user_homework.user_homework_checks.first()
        if user_homework_check:
            AudioFile.objects.create(
                file=instance.file,
                user_homework_check=user_homework_check,
            )
