from django.apps import AppConfig


class CommonServicesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "common_services"

    def ready(self):
        from common_services.models import AudioFile, TextFile
        from common_services.signals import (
            copy_audio_file_to_homework_check,
            copy_text_file_to_homework_check,
        )
        from django.db.models.signals import post_save

        post_save.connect(copy_text_file_to_homework_check, sender=TextFile)
        post_save.connect(copy_audio_file_to_homework_check, sender=AudioFile)
