from rest_framework import serializers

from lesson_tests.models import LessonTest


class TestSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели теста
    """

    class Meta:
        model = LessonTest
        fields = "__all__"
