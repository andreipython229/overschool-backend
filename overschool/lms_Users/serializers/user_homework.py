from rest_framework import serializers

from lms_User.models import UserHomework


class UserHomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели выполненной домашней работы
    """

    class Meta:
        model = UserHomework
        fields = '__all__'


