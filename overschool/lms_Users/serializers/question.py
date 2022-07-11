from rest_framework import serializers

from lms_Users.models import Question


class QuestionSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели вопроса
    """

    class Meta:
        model = Question
        fields = '__all__'