from rest_framework import serializers

from lesson_tests.models import UserTest


class UserTestSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели выполненного теста
    """

    class Meta:
        model = UserTest
        fields = "__all__"
