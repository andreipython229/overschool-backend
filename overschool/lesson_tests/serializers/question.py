from rest_framework import serializers

from overschool.lesson_tests.models import Question


class QuestionSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели вопроса
    """

    class Meta:
        model = Question
        fields = "__all__"
