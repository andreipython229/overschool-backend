from rest_framework import serializers

from courses.models import Lesson
from common_services.serializers import TextFileSerializer, AudioFileSerializer


class LessonSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели урока
    """
    audio_files = AudioFileSerializer(many=True, required=False)
    text_files = TextFileSerializer(many=True, required=False)
    type = serializers.CharField(default="lesson", read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "lesson_id",
            "section",
            "name",
            "order",
            "description",
            "video",
            "points",
            "text_files",
            "audio_files",
            "type"
        ]
        read_only_fields = ["type", "text_files", "audio_files"]
