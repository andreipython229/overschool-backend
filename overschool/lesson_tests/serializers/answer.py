from lesson_tests.models import Answer
from rest_framework import serializers


class AnswerSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели ответа
    """

    class Meta:
        model = Answer
        fields = "__all__"
