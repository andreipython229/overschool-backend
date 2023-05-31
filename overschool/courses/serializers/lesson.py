from common_services.serializers import AudioFileGetSerializer, TextFileGetSerializer
from courses.models import Lesson
from rest_framework import serializers


class LessonSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели урока
    """

    type = serializers.CharField(default="lesson", read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "lesson_id",
            "section",
            "name",
            "order",
            "author_id",
            "description",
            "video",
            "points",
            "type",
        ]


class LessonDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для просмотра конкретного урока
    """

    audio_files = AudioFileGetSerializer(many=True, required=False)
    text_files = TextFileGetSerializer(many=True, required=False)
    type = serializers.CharField(default="lesson", read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "lesson_id",
            "section",
            "name",
            "order",
            "author_id",
            "description",
            "video",
            "points",
            "text_files",
            "audio_files",
            "type",
        ]
        read_only_fields = ["type", "text_files", "audio_files"]
