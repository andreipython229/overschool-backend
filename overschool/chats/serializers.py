from common_services.selectel_client import UploadToS3
from django.contrib.auth import get_user_model
from django.db.models import Max
from rest_framework import serializers

from .models import Chat, Message, UserChat

User = get_user_model()
s3 = UploadToS3()


class UserChatSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "avatar",
            "email",
            "first_name",
            "last_name",
            "id",
            "username",
            # "phone_number",
        ]

    def get_avatar(self, obj):
        if obj.profile.avatar:
            return s3.get_link(obj.profile.avatar.name)
        else:
            # Если нет загруженной фотографии, вернуть ссылку на базовую аватарку
            base_avatar_path = "users/avatars/base_avatar.jpg"
            return s3.get_link(base_avatar_path)


class UserChatRoleSerializer(serializers.ModelSerializer):
    user = UserChatSerializer()

    class Meta:
        model = UserChat
        fields = [
            "user_role",
            "user",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {"user_role": data["user_role"], **data["user"]}


class ChatSerializer(serializers.ModelSerializer):
    senders = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = [
            "id",
            "created_at",
            "is_deleted",
            "name",
            "type",
            "last_message",
            "senders",
            "unread",
        ]
        read_only_fields = ["is_deleted"]

    def get_senders(self, obj):
        user_chats = obj.userchat_set.all()
        serializer = UserChatRoleSerializer(user_chats, many=True)
        return serializer.data

    def get_last_message(self, obj):
        last_message = obj.message_set.aggregate(max_sent_at=Max("sent_at"))[
            "max_sent_at"
        ]
        if last_message:
            message = obj.message_set.filter(sent_at=last_message).first()
            serializer = MessageGetSerializer(
                message, context={"request": self.context["request"]}
            )
            return serializer.data
        return None

    def get_unread(self, obj):
        return 0


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "sent_at",
            "content",
            "file",
        ]


class MessageGetSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "sent_at",
            "content",
            "file",
        ]

    def get_file(self, obj):
        return s3.get_link(obj.file.name) if obj.file else None


class MessageInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "sent_at",
            "content",
        ]
