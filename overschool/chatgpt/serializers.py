from rest_framework import serializers
from .models import GptMessage


class GptMessageSerializer(ModelSerializer):
    class Meta:
        model = GptMessage
        fields = [
            "sedner",
            "sedner_question",
            "answer",
            "date",
        ]
