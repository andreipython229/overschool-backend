from datetime import datetime

from courses.models import StudentsGroup
from rest_framework import serializers
from users.models import User

from .students_group_settings import StudentsGroupSettingsSerializer


class StudentsGroupSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели группы студентов
    """

    group_settings = StudentsGroupSettingsSerializer(required=False)
    students = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, required=False
    )

    class Meta:
        model = StudentsGroup
        fields = [
            "name",
            "group_id",
            "course_id",
            "teacher_id",
            "students",
            "group_settings",
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        view = self.context.get("view")
        course = attrs.get("course_id")
        students = attrs.get("students")
        teacher = attrs.get("teacher_id")

        if request.method == "POST" and not course:
            raise serializers.ValidationError("Курс должен быть указан.")

        if request.method == "POST" and not teacher:
            raise serializers.ValidationError(
                "Поле 'teacher_id' обязательно для заполнения."
            )
        elif teacher in students:
            raise serializers.ValidationError(
                "Учитель не может учиться в группе, в которой преподает."
            )

        if students:
            duplicate_count = 0
            if request.method == "POST":
                duplicate_count = StudentsGroup.objects.filter(
                    course_id=course, students__in=students
                ).count()
            elif request.method in ["PUT", "PATCH"]:
                duplicate_count = (
                    StudentsGroup.objects.filter(
                        course_id=course, students__in=students
                    )
                    .exclude(pk=view.get_object().pk)
                    .count()
                )
            if duplicate_count > 0:
                raise serializers.ValidationError(
                    "Убедитесь, что каждый пользователь в группах курса уникален."
                )

        return attrs

    def update(self, instance, validated_data):
        group_settings_data = validated_data.pop("group_settings", None)
        instance = super().update(instance, validated_data)

        if group_settings_data:
            group_settings = instance.group_settings
            for key, value in group_settings_data.items():
                setattr(group_settings, key, value)
            group_settings.save()

        return instance


class GroupStudentsSerializer(serializers.Serializer):
    """
    Сериализатор для статы юзеров
    """

    group_id = serializers.IntegerField(help_text="Номер группы", required=False)

    class Meta:
        fields = "__all__"


class GroupUsersByMonthSerializer(serializers.Serializer):
    """
    Сериализатор для кол-ва юзеров по месяцу
    """

    group_id = serializers.IntegerField(help_text="Номер группы", required=False)
    month_number = serializers.IntegerField(
        help_text="Номер месяца, за который хотите получить статистику",
        required=False,
        default=datetime.now().month,
    )

    class Meta:
        fields = "__all__"


class GroupsInCourseSerializer(serializers.ModelSerializer):
    """
    Сериализатор для передачи групп вместе с курсами
    """

    class Meta:
        model = StudentsGroup
        fields = ["group_id", "name", "teacher_id", "type"]
