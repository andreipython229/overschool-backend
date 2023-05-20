from common_services.models import AudioFile
from rest_framework import serializers


class AudioFileSerializer(serializers.ModelSerializer):
    """
    Сериализатор моедли аудио файлов
    """

    class Meta:
        model = AudioFile
        fields = [
            "id",
            "order",
            "description",
            "file",
            "file_url",
            "author",
            "base_lesson",
            "user_homework",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        if not attrs.get("base_lesson") and not attrs.get("user_homework"):
            raise serializers.ValidationError("Укажите base_lesson либо user_homework")
        return attrs
