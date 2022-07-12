from rest_framework import serializers

from lesson_tests.models import Answer


class AnswerSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели ответа
    """

    class Meta:
        model = Answer
        fields = "__all__"
