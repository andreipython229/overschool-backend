from common_services.models import TextFile
from common_services.selectel_client import get_selectel_link
from rest_framework import serializers


class TextFileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания текстовых файлов
    """

    class Meta:
        model = TextFile
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


class TextFileGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения текстовых файлов
    """

    file = serializers.SerializerMethodField(method_name="get_file_link")

    class Meta:
        model = TextFile
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
        return get_selectel_link(str(obj.file))
