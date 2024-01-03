from django.db import models
from users.models.user import User


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

