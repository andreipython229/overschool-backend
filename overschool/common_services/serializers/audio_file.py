from rest_framework import serializers

from common_services.models import AudioFile


class AudioFileSerializer(serializers.ModelSerializer):
    """
    Сериализатор моедли аудио файлов
    """

    class Meta:
        model = AudioFile
        fields = "__all__"
