from datetime import datetime

from rest_framework import serializers

from courses.models import StudentsGroup
# from users.models.user import User
# from django.db import models

class StudentsGroupSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели группы студентов
    """

    class Meta:
        model = StudentsGroup
        fields = "__all__"

    def validate_teacher_id(self, value):
        if not value.groups.filter(name="Teacher").exists():
            raise serializers.ValidationError(
                "Пользователь указанный в поле 'teacher_id' не является учителем.")
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        if request.method == 'POST':
            if 'teacher_id' not in attrs:
                raise serializers.ValidationError("Поле 'teacher_id' обязательно для заполнения.")
            self.validate_teacher_id(attrs['teacher_id'])
        elif request.method in ['PUT', 'PATCH']:
            if 'teacher_id' in attrs:
                self.validate_teacher_id(attrs['teacher_id'])
        return attrs

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
