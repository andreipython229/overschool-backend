from common_services.serializers import AudioFileGetSerializer, TextFileGetSerializer
from courses.models import Homework
from courses.models.homework.user_homework import UserHomework
from courses.models.homework.user_homework_check import UserHomeworkCheck
from courses.serializers.user_homework_check import UserHomeworkCheckDetailSerializer
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
    user_mark = serializers.SerializerMethodField()
    user_homework_checks = serializers.SerializerMethodField()

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
            "user_mark",
            "user_homework_checks",
        ]
        read_only_fields = [
            "type",
            "text_files",
            "audio_files",
            "user_homework_checks",
            "user_mark",
        ]

    def get_user_homework_checks(self, obj):
        user = self.context["request"].user
        user_homework_checks = UserHomeworkCheck.objects.filter(
            user_homework__homework=obj, user_homework__user=user
        ).order_by("-created_at")
        if user_homework_checks:
            serializer = UserHomeworkCheckDetailSerializer(
                user_homework_checks, many=True
            )
            return serializer.data
        return None

    def get_user_mark(self, obj):
        user = self.context["request"].user
        user_mark_exists = UserHomework.objects.filter(homework=obj, user=user).exists()
        if user_mark_exists:
            return UserHomework.objects.get(homework=obj, user=user).mark
        return None
