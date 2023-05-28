from common_services.serializers import AudioFileSerializer, TextFileGetSerializer
from courses.models import Lesson
from rest_framework import serializers


class LessonSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели урока
    """

    # audio_files = AudioFileSerializer(many=True, required=False)
    # # text_files = TextFileSerializer(many=True, required=False)
    # text_files = TextFileGetSerializer(many=True, required=False)
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
            # "text_files",
            # "audio_files",
            "type",
        ]
        # read_only_fields = ["type", "text_files", "audio_files"]


class LessonDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для просмотра конкретного урока
    """

    audio_files = AudioFileSerializer(many=True, required=False)
    # text_files = TextFileSerializer(many=True, required=False)
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
