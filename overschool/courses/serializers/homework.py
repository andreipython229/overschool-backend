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
    """
    Сериализатор просмотра конкретного домашнего задания
    """

    last_check_status = serializers.CharField(source='last_check_status', read_only=True)
    last_check_response = serializers.CharField(source='last_check_response', read_only=True)
    last_check_time = serializers.DateTimeField(source='last_check_time', read_only=True)
    last_check_teacher_avatar = serializers.ImageField(source='last_check_teacher_avatar', read_only=True)
    last_check_teacher_name = serializers.CharField(source='last_check_teacher_name', read_only=True)
    last_check_teacher_lastname = serializers.CharField(source='last_check_teacher_lastname', read_only=True)

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
        read_only_fields = ["type", "audio_files", "text_files"]