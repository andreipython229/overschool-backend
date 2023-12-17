from rest_framework import serializers
from .models import GptMessage


class GptMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GptMessage
        fields = [
            "sender",
            "sender_question",
            "answer",
            "message_date",
        ]
