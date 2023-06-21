import yadisk
from common_services.models import AudioFile
from common_services.yandex_client import get_yandex_link
from rest_framework import serializers


class AudioFileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания аудио файлов
    """

    class Meta:
        model = AudioFile
        fields = [
            "id",
            "file",
            "file_url",
            "author",
            "base_lesson",
            "user_homework",
            "user_homework_check",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["author"]

    def validate(self, attrs):
        if (
            not attrs.get("base_lesson")
            and not attrs.get("user_homework")
            and not attrs.get("user_homework_check")
        ):
            raise serializers.ValidationError(
                "Укажите base_lesson либо user_homework либо user_homework_check"
            )
        return attrs


class AudioFileGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения аудио файлов
    """

    file = serializers.SerializerMethodField(method_name="get_file_link")

    class Meta:
        model = AudioFile
        fields = [
            "id",
            "file",
            "file_url",
            "author",
            "base_lesson",
            "user_homework",
            "user_homework_check",
            "created_at",
            "updated_at",
        ]

    def get_file_link(self, obj):
        return get_yandex_link(str(obj.file))
