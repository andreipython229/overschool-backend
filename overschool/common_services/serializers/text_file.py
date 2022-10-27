from rest_framework import serializers

from common_services.models import TextFile


class TextFileSerializer(serializers.ModelSerializer):
    """
    Сериализатор моедли текстовых файлов
    """

    class Meta:
        model = TextFile
        fields = [
            "id",
            "order",
            "description",
            "file",
            "author",
            "base_lesson",
            "user_homework",
            "created_at",
            "updated_at"
        ]

    def validate(self, attrs):
        if not attrs.get("base_lesson") and not attrs.get("user_homework"):
            raise serializers.ValidationError("Укажите base_lesson либо user_homework")
        return attrs
