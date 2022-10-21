from rest_framework import serializers

from courses.models import UserTest


class UserTestSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели выполненного теста
    """

    class Meta:
        model = UserTest
        fields = "__all__"
