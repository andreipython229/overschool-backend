from rest_framework import serializers

from .models import Chat, Message


class ChatSerializer(serializers.ModelSerializer):

    class Meta:
        model = Chat
        fields = (
            'id',
            'is_deleted',
            'created_at',
        )
        # для того, чтобы параметры были необязательным
        read_only_fields = ['is_deleted',]


class MessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = (
            'id',
            'sender',
            'sent_at',
            'content',
        )
