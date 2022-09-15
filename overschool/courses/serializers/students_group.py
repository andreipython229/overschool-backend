from rest_framework import serializers

from courses.models import StudentsGroup
from datetime import datetime


class StudentsGroupSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели группы студентов
    """

    class Meta:
        model = StudentsGroup
        fields = "__all__"


class GroupStudentsSerializer(serializers.Serializer):
    """
    Сериализатор для статы юзеров
    """
    group_id = serializers.IntegerField(help_text="Номер группы")

    class Meta:
        fields = '__all__'


class GroupUsersByMonthSerializer(serializers.Serializer):
    """
    Сериализатор для кол-ва юзеров по месяцу
    """
    group_id = serializers.IntegerField(help_text="Номер группы")
    month_number = serializers.IntegerField(help_text="Номер месяца, за который хотите получить статистику",
                                            required=False, default=datetime.now().month)

    class Meta:
        fields = '__all__'
