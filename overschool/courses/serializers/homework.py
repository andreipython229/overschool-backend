from rest_framework import serializers

from courses.models import Homework
from common_services.serializers import TextFileSerializer, AudioFileSerializer


class HomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор моедли домашнего задания
    """
    audio_files = AudioFileSerializer(many=True, required=False)
    text_files = TextFileSerializer(many=True, required=False)
    type = serializers.CharField(default="homework", read_only=True)

    class Meta:
        model = Homework
        fields = [
            "homework_id",
            "section",
            "name",
            "order",
            "author_id",
            "description",
            "automate_accept",
            "time_accept",
            "points",
            "text_files",
            "audio_files",
            "type"
        ]
        read_only_fields = ["type", "text_files", "audio_files"]
