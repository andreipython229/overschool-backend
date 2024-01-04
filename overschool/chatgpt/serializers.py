from rest_framework import serializers
from .models import UserMessage, BotResponse


class BotResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotResponse
        fields = [
            "sender",
            "answer",
            "message_date",
        ]


class UserMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMessage
        fields = [
            "sender",
            "sender_question",
            "message_date",
        ]
