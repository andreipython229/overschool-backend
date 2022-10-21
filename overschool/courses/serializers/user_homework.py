from datetime import date

from rest_framework import serializers

from courses.models import UserHomework


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
            "file",
            "file_url",
            "teacher",
            "teacher_message",
        ]
        read_only_fields = (
            "user",
            "status",
            "mark",
            "teacher_message",
            "teacher",
        )


class TeacherHomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели выполненной домашней работы со стороны преподавателя
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
            "file",
            "file_url",
            "teacher",
            "teacher_message",
        ]
        read_only_fields = (
            "user",
            "file",
            "text",
            "teacher",
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
