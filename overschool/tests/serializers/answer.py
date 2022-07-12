from rest_framework import serializers

from tests.models import Answer



class AnswerSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели ответа
    """

    class Meta:
        model = Answer
        fields = '__all__'
