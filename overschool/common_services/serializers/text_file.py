import yadisk
from common_services.models import TextFile
from common_services.yandex_client import get_yandex_link
from rest_framework import serializers


class TextFileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания текстовых файлов
    """

    class Meta:
        model = TextFile
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


class TextFileGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения текстовых файлов
    """

    file = serializers.SerializerMethodField(method_name="get_file_link")

    class Meta:
        model = TextFile
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

    def get_file_link(self, obj):
        return get_yandex_link(str(obj.file))
