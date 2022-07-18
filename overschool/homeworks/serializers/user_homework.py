from homeworks.models import UserHomework
from rest_framework import serializers


class UserHomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели выполненной домашней работы
    """

    class Meta:
        model = UserHomework
        fields = "__all__"
