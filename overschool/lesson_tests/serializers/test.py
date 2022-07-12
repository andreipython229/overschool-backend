from rest_framework import serializers

from lesson_tests.models import Test


class TestSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели теста
    """

    class Meta:
        model = Test
        fields = "__all__"
