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
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = [
            "id",
            "name",
            "is_deleted",
            "created_at",
            "type",
            "unread_count",
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
            serializer = MessageSerializer(message, context={'request': self.context['request']})
            return serializer.data
        return None

    def get_unread_count(self, obj):
        user = self.context['request'].user

        unread_count = obj.message_set.exclude(read_by=user).count()
        return unread_count


class MessageSerializer(serializers.ModelSerializer):
    read_by = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "read_by",
            "sent_at",
            "content",
        ]

    def get_read_by(self, obj):
        if self.context['request'].user in obj.read_by.all():
            return True
        else:
            return False


class MessageInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "sent_at",
            "content",
        ]


class ChatInfoSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    senders = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = [
            "id",
            "name",
            "type",
            "is_deleted",
            "unread_count",
            "senders",
            "last_message",
        ]

    def get_last_message(self, obj):
        last_message = obj.message_set.aggregate(max_sent_at=Max('sent_at'))['max_sent_at']
        if last_message:
            message = obj.message_set.filter(sent_at=last_message).first()
            serializer = MessageInfoSerializer(message)
            return serializer.data
        return None

    def get_unread_count(self, obj):
        user = self.context['request'].user

        unread_count = obj.message_set.exclude(read_by=user).count()
        return unread_count

    def get_senders(self, obj):
        user_chats = obj.userchat_set.all()
        users = [user_chat.user for user_chat in user_chats]
        serializer = UserChatSerializer(users, many=True)
        return serializer.data
