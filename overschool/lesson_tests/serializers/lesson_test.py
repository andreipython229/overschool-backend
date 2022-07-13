from lesson_tests.models import LessonTest
from rest_framework import serializers


class TestSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели теста
    """

    class Meta:
        model = LessonTest
        fields = "__all__"
