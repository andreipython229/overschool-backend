from common_services.serializers import AudioFileGetSerializer, TextFileGetSerializer
from courses.models import UserHomework
from courses.models.homework.user_homework_check import UserHomeworkCheck
from courses.serializers.user_homework_check import UserHomeworkCheckDetailSerializer
from rest_framework import serializers


class UserHomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели выполненной домашней работы со стороны ученика
    """

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
        ]
        read_only_fields = (
            "user",
            "status",
            "mark",
            "teacher",
        )


class UserHomeworkDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для просмотра конкретной выполненной домашней работы со стороны ученика
    """

    audio_files = AudioFileGetSerializer(many=True, required=False)
    text_files = TextFileGetSerializer(many=True, required=False)
    user_homework_checks = serializers.SerializerMethodField()
    homework_name = serializers.CharField(source="homework.name", read_only=True)
    last_reply = serializers.SerializerMethodField()
    teacher_first_name = serializers.CharField(
        source="teacher.first_name", read_only=True
    )
    teacher_last_name = serializers.CharField(
        source="teacher.last_name", read_only=True
    )
    teacher_avatar = serializers.CharField(
        source="teacher.profile.avatar", read_only=True
    )

    class Meta:
        model = UserHomework
        fields = [
            "user_homework_id",
            "created_at",
            "updated_at",
            "user",
            "homework",
            "homework_name",
            "last_reply",
            "text",
            "status",
            "mark",
            "teacher",
            "teacher_first_name",
            "teacher_last_name",
            "teacher_avatar",
            "text_files",
            "audio_files",
            "user_homework_checks",
        ]
        read_only_fields = (
            "user",
            "status",
            "mark",
            "teacher",
            "text_files",
            "audio_files",
            "user_homework_checks",
            "homework_name",
            "last_reply",
            "teacher_first_name",
            "teacher_last_name",
            "teacher_avatar",
        )

    def get_user_homework_checks(self, obj):
        user_homework_checks = UserHomeworkCheck.objects.filter(
            user_homework=obj
        ).order_by("-created_at")
        serializer = UserHomeworkCheckDetailSerializer(user_homework_checks, many=True)
        return serializer.data

    def get_last_reply(self, obj):
        user_homework_checks = UserHomeworkCheck.objects.filter(
            user_homework=obj
        ).last()
        if user_homework_checks:
            serializer = UserHomeworkCheckDetailSerializer(user_homework_checks)
            return serializer.data
        return None


class UserHomeworkStatisticsSerializer(serializers.ModelSerializer):
    """
    Сериализатор для статистики по сданным домашним заданиям
    """

    homework_name = serializers.CharField(source="homework.name", read_only=True)
    user_first_name = serializers.CharField(source="user.first_name", read_only=True)
    user_last_name = serializers.CharField(source="user.last_name", read_only=True)
    user_avatar = serializers.CharField(source="user.profile.avatar", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)
    course_name = serializers.CharField(
        source="homework.section.course.name", read_only=True
    )
    group_id = serializers.SerializerMethodField()
    last_reply = serializers.SerializerMethodField()

    class Meta:
        model = UserHomework
        fields = [
            "user_homework_id",
            "user",
            "user_first_name",
            "user_last_name",
            "user_email",
            "user_avatar",
            "homework",
            "homework_name",
            "course_name",
            "group_id",
            "status",
            "mark",
            "last_reply",
        ]
        read_only_fields = fields

    def get_last_reply(self, obj):
        user_homework_checks = UserHomeworkCheck.objects.filter(
            user_homework=obj
        ).last()
        if user_homework_checks:
            return user_homework_checks.updated_at
        return None

    def get_group_id(self, obj):
        group = obj.user.students_group_fk.get(
            course_id=obj.homework.section.course.course_id
        )
        if group:
            return group.group_id
        return None
