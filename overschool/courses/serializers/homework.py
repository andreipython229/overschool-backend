from common_services.serializers import AudioFileGetSerializer, TextFileGetSerializer
from courses.models import Homework
from rest_framework import serializers


class HomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели домашнего задания
    """

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
            "video",
            "automate_accept",
            "time_accept",
            "points",
            "type",
        ]


class HomeworkDetailSerializer(serializers.ModelSerializer):
    audio_files = AudioFileGetSerializer(many=True, required=False)
    text_files = TextFileGetSerializer(many=True, required=False)
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
            "video",
            "automate_accept",
            "time_accept",
            "points",
            "text_files",
            "audio_files",
            "type",
        ]
        read_only_fields = ["type", "text_files", "audio_files"]


class HomeworkHistorySerializer(serializers.Serializer):
    class Meta:
        fields = [
            "homework_id",
            "section",
            "name",
            "order",
            "author_id",
            "description",
            "video",
            "automate_accept",
            "time_accept",
            "points",
            "user_homeworks__text",
            "audio_files",
            "type",
            "last_check_status",
            "last_check_response",
            "last_check_time",
            "last_check_teacher_avatar",
            "last_check_teacher_name",
            "last_check_teacher_lastname",
            "text_files"
        ]
