from rest_framework import serializers

from lesson_test.models import LessonTest


class TestSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели теста
    """

    class Meta:
        model = LessonTest
        fields = "__all__"
