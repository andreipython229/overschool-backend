from django.db import models
from users.models.user import User


class GptMessage(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Отправитель сообщения'
    )
    sedner_question = models.TextField(
        verbose_name="Контент сообщения"
    )
    answer = models.TextField(
        verbose_name="Ответчик"
    )
    message_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата сообщения"
    )

    def __str__(self):
        return f'{self.sender.username} send message {self.sedner_question} ({self.date})'
