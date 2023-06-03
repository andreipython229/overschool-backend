import uuid

from users.models.user import User
from django.db import models
from django.db.models import Q
from django.urls import reverse


class Chat(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        max_length=255,
        default=""
    )
    is_deleted = models.BooleanField(
        default=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return str(self.id)

    def get_absolute_url(self):
        return reverse('chat_detail', args=[str(self.id)])


class Message(models.Model):
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="masseges"
    )
    sent_at = models.DateTimeField(
        auto_now_add=True
    )
    content = models.TextField()

    def __str__(self):
        return self.content


# many-to-many
class UserChat(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chats"
    )
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.user.__str__()} - {self.chat.__str__()}"

    @classmethod
    def get_existed_chat_id(cls, chat_creator, reciever):
        chats = cls.objects.filter(
            Q(user=chat_creator) | Q(user=reciever)
        )
        chats_list = [str(chat.chat) for chat in chats]
        seen_chats = set()
        existed_chat = [chat for chat in chats_list if chat in seen_chats or seen_chats.add(chat)]
        if existed_chat:
            return existed_chat[0]
        else:
            return False
