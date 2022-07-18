from lesson_tests.models import Question
from rest_framework import serializers


class QuestionSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели вопроса
    """

    class Meta:
        model = Question
        fields = "__all__"
