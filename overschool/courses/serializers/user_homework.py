from datetime import date

from rest_framework import serializers

from courses.models import UserHomework
from common_services.serializers import TextFileSerializer, AudioFileSerializer


class AllUserHomeworkSerializer(serializers.ModelSerializer):
    audio_files = AudioFileSerializer(many=True, required=False)
    text_files = TextFileSerializer(many=True, required=False)
    status = serializers.CharField(max_length=20, help_text="Статус работы", required=False)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    profile_avatar = serializers.ImageField(source='user.avatar', read_only=True)

    class Meta:
        model = UserHomework
        fields = ['audio_files', 'text_files', 'status', 'user_first_name', 'user_last_name', 'profile_avatar']



class UserHomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели выполненной домашней работы со стороны ученика
    """
    audio_files = AudioFileSerializer(many=True, required=False)
    text_files = TextFileSerializer(many=True, required=False)

    class Meta:
        model = UserHomework
        fields = [
            "user_homework_id",
            "created_at",
            "updated_at",
            "user",
            "homework",
            "text",
            "status",
            "mark",
            "teacher",
            "teacher_message",
            "text_files",
            "audio_files",
        ]
        read_only_fields = (
            "user",
            "status",
            "mark",
            "teacher_message",
            "teacher",
            "text_files",
            "audio_files",
        )


class TeacherHomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели выполненной домашней работы со стороны преподавателя
    """
    audio_files = AudioFileSerializer(many=True, required=False)
    text_files = TextFileSerializer(many=True, required=False)
    teacher_first_name = serializers.CharField(
        source="teacher.first_name", read_only=True
    )
    teacher_last_name = serializers.CharField(
        source="teacher.last_name", read_only=True
    )

    class Meta:
        model = UserHomework
        fields = [
            "user_homework_id",
            "created_at",
            "updated_at",
            "user",
            "homework",
            "text",
            "status",
            "mark",
            "teacher",
            "teacher_first_name",
            "teacher_last_name",
            "teacher_message",
            "text_files",
            "audio_files",
        ]
        read_only_fields = (
            "user",
            "text",
            "teacher",
            "text_files",
            "audio_files",
        )


class UserHomeworkStatisticsSerializer(serializers.Serializer):
    """
    Сериализатор для статистики по сданным домашним заданиям
    """

    start_date = serializers.DateField(
        help_text="С какой даты показать записи",
        default=date(2014, 1, 1),
        required=False,
    )
    end_date = serializers.DateField(
        help_text="До какой даты показать записи",
        required=False,
        default=date(2200, 1, 1),
    )
    status = serializers.CharField(
        max_length=20, help_text="Статус работы", required=False, default=None
    )
    start_mark = serializers.IntegerField(help_text="Оценка от", required=False)
    end_mark = serializers.IntegerField(help_text="Оценка до", required=False)
    course_id = serializers.IntegerField(
        help_text="Id курса", default=None, required=False
    )
    group_id = serializers.IntegerField(
        help_text="Id группы", required=False, default=None
    )
    homework_id = serializers.IntegerField(
        help_text="Id домашней работы", required=False, default=None
    )

    class Meta:
        fields = "__all__"
