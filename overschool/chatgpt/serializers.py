from rest_framework import serializers
from .models import UserMessage, BotResponse, OverAiChat


class BotResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotResponse
        fields = [
            "sender",
            "answer",
            "message_date",
            "overai_chat_id",
        ]


class UserMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMessage
        fields = [
            "sender",
            "sender_question",
            "message_date",
            "overai_chat_id",
        ]


class OverAiChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = OverAiChat
        fields = [
            "user_id",
        ]
