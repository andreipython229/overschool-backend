from common_services.models import AudioFile
from common_services.selectel_client import UploadToS3
from rest_framework import serializers

s3 = UploadToS3()


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
        read_only_fields = ["author", "file"]

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


class AudioFileCheckSerializer(serializers.ModelSerializer):
    """
    Сериализатор для проверки каждого добавляемого аудио файла в отдельности
    """

    file = serializers.SerializerMethodField(method_name="get_file_link")
    size = serializers.SerializerMethodField(method_name="get_file_size")

    class Meta:
        model = AudioFile
        fields = [
            "id",
            "file",
            "size",
            "file_url",
            "author",
            "base_lesson",
            "user_homework",
            "user_homework_check",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["author", "file", "size"]

    def get_file_link(self, obj):
        return s3.get_link(obj.file.name)

    def get_file_size(self, obj):
        file_size = s3.get_size_object(obj.file.name)
        return file_size


class AudioFileGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения аудио файлов
    """

    file = serializers.SerializerMethodField(method_name="get_file_link")
    size = serializers.SerializerMethodField(method_name="get_file_size")

    class Meta:
        model = AudioFile
        fields = [
            "id",
            "file",
            "file_url",
            "size",
            "author",
            "base_lesson",
            "user_homework",
            "user_homework_check",
            "created_at",
            "updated_at",
        ]

    def get_file_link(self, obj):
        return s3.get_link(obj.file.name)

    def get_file_size(self, obj):
        file_size = s3.get_size_object(obj.file.name)
        return file_size
