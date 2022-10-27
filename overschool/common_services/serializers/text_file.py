from rest_framework import serializers

from common_services.models import TextFile


class TextFileSerializer(serializers.ModelSerializer):
    """
    Сериализатор моедли текстовых файлов
    """

    class Meta:
        model = TextFile
        fields = "__all__"
