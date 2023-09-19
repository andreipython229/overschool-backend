from django.db.models import Max
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Chat, Message
from common_services.selectel_client import SelectelClient

User = get_user_model()
s = SelectelClient()


class UserChatSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "avatar",
        ]

    def get_avatar(self, obj):
        if obj.profile.avatar:
            return s.get_selectel_link(str(obj.profile.avatar))
        else:
            # Если нет загруженной фотографии, вернуть ссылку на базовую аватарку
            base_avatar_path = "/users/avatars/base_avatar.jpg"
            return s.get_selectel_link(base_avatar_path)


class ChatSerializer(serializers.ModelSerializer):
    senders = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = [
            "id",
            "name",
            "is_deleted",
            "created_at",
            "senders",
            "last_message",
        ]
        read_only_fields = ['is_deleted']

    def get_senders(self, obj):
        user_chats = obj.userchat_set.all()
        users = [user_chat.user for user_chat in user_chats]
        serializer = UserChatSerializer(users, many=True)
        return serializer.data

    def get_last_message(self, obj):
        last_message = obj.message_set.aggregate(max_sent_at=Max('sent_at'))['max_sent_at']
        if last_message:
            message = obj.message_set.filter(sent_at=last_message).first()
            serializer = MessageSerializer(message)
            return serializer.data
        return None


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "is_read",
            "sent_at",
            "content",
        ]
