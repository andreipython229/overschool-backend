from django.db import models
from users.models.user import User


class OverAiChat(models.Model):
    chat_name = models.TextField(
        verbose_name="Имя чата",
        default="Новый чат"
    )
    user_id = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Идентификатор пользователя'
    )


class UserMessage(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Отправитель сообщения'
    )
    sender_question = models.TextField(
        verbose_name="Контент сообщения"
    )
    message_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата сообщения"
    )
    overai_chat_id = models.ForeignKey(
        OverAiChat,
        on_delete=models.CASCADE,
        verbose_name="Идентификатор чата"
    )


class BotResponse(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Отправитель сообщения'
    )
    answer = models.TextField(
        verbose_name="Ответ бота"
    )
    message_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата ответа"
    )
    overai_chat_id = models.ForeignKey(
        OverAiChat,
        on_delete=models.CASCADE,
        verbose_name="Идентификатор чата"
    )


class AIProvider(models.Model):
    name = models.CharField(max_length=70)
    provider_type = models.CharField(max_length=40)

    def __str__(self):
        return self.name

