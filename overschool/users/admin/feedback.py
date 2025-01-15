import time

from common_services.selectel_client import UploadToS3
from django.contrib import admin
from users.models import Feedback

s3 = UploadToS3()


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    """
    Админка для управления отзывами.
    """

    list_display = ("name", "surname", "position", "rating", "created_at")
    readonly_fields = ("created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        """
        Переопределяем метод сохранения, чтобы загружать аватар в S3.
        """
        # Проверяем, есть ли новый файл в форме
        avatar = request.FILES.get("avatar")
        if avatar:
            # Удаляем старый файл из S3, если он существует
            if obj.pk and obj.avatar:
                s3.delete_file(obj.avatar)

            # Используем текущее время для генерации уникального имени файла
            current_time = int(time.time())  # Текущее время в секундах
            obj.avatar = s3.upload_avatar_feedback(avatar, current_time)

        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        """
        Переопределяем метод удаления, чтобы удалять аватар из S3.
        """
        # Удаляем файл аватара из S3, если он есть
        if obj.avatar:
            s3.delete_file(obj.avatar)

        super().delete_model(request, obj)
