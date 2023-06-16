from datetime import datetime
from django.db.models import Count
from rest_framework import serializers

from courses.models import StudentsGroup, StudentsGroupSettings
# from users.models.user import User
# from django.db import models
from .students_group_settings import StudentsGroupSettingsSerializer


class StudentsGroupSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели группы студентов
    """
    group_settings = StudentsGroupSettingsSerializer(required=False)

    class Meta:
        model = StudentsGroup
        fields = "__all__"

    def validate(self, attrs):
        request = self.context.get('request')
        course = attrs.get('course_id')
        students = attrs.get('students')
        teacher = attrs.get('teacher_id')

        self.validate_teacher(self, request=request, teacher=teacher)

        if not course:
            raise serializers.ValidationError("Курс должен быть указан.")

        if students:
            duplicate_count = StudentsGroup.objects.filter(course_id=course, students__in=students).count()
            if duplicate_count > 0:
                raise serializers.ValidationError("Убедитесь, что каждый пользователь в группах курса уникален.")

        for student in students:
            if not student.groups.filter(name="Student").exists():
                raise serializers.ValidationError("Все пользователи в списке 'students' должны быть студентами.")
        return attrs

    def update(self, instance, validated_data):
        group_settings_data = validated_data.pop('group_settings', None)
        instance = super().update(instance, validated_data)

        if group_settings_data:
            group_settings = instance.group_settings
            for key, value in group_settings_data.items():
                setattr(group_settings, key, value)
            group_settings.save()

        return instance

    @staticmethod
    def validate_teacher(self, request, teacher):
        if request.method == 'POST' and not teacher:
            raise serializers.ValidationError("Поле 'teacher_id' обязательно для заполнения.")
        elif request.method in ['POST', 'PUT', 'PATCH'] and teacher:
            if not teacher.groups.filter(name="Teacher").exists():
                raise serializers.ValidationError(
                    "Пользователь указанный в поле 'teacher_id' не является учителем.")

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
