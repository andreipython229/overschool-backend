import uuid

from django.db import models
from django.db.models import Q
from django.urls import reverse
from users.models.user import User


class Chat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, default="")
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    TYPE_CHOICES = (
        ("GROUP", "Group"),
        ("PERSONAL", "Personal"),
        ("COURSE", "Course"),
        ("ADMIN", "Admin"),
    )

    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default=None,
    )
    personal_chats = models.ManyToManyField(
        "Chat",
        through="ChatLink",
        symmetrical=False,
        related_name="group_chats",
        blank=True,
    )

    def __str__(self):
        return str(self.id)

    def get_absolute_url(self):
        return reverse("chat_detail", args=[str(self.id)])

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["type"]),
        ]


class ChatLink(models.Model):
    parent = models.ForeignKey(Chat, related_name="links_to", on_delete=models.CASCADE)
    child = models.ForeignKey(Chat, related_name="links_from", on_delete=models.CASCADE)


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    sent_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

    def __str__(self):
        return self.content

    class Meta:
        verbose_name = "Сообщение чата"
        verbose_name_plural = "Сообщения чата"
        indexes = [
            models.Index(fields=["chat"]),
            models.Index(fields=["sender"]),
        ]


# many-to-many
class UserChat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chats")
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    user_role = models.CharField(verbose_name="Роль пользователя", max_length=50)
    unread_messages_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.__str__()} - {self.chat.__str__()}"

    class Meta:
        verbose_name = "Пользователь чата"
        verbose_name_plural = "Пользователи чата"
        indexes = [
            models.Index(fields=["chat"]),
            models.Index(fields=["user"]),
            models.Index(fields=["user_role"]),
        ]

    @classmethod
    def get_existed_chat_id(cls, chat_creator, reciever):
        chat_id = (
            cls.objects.filter(user__in=[chat_creator, reciever])
            .values_list("chat__id", flat=True)
            .distinct()
            .first()
        )

        return str(chat_id) if chat_id is not None else False

    @classmethod
    def get_existed_chat_id_by_type(cls, chat_creator, reciever, type):
        chat_id = (
            cls.objects.filter(
                user=chat_creator, chat__type=type, chat__userchat__user=reciever
            )
            .values_list("chat__id", flat=True)
            .first()
        )

        return str(chat_id) if chat_id is not None else False
