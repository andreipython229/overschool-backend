from django.db import models

from overschool.abstract_models import TimeStampedModel
from users.models import SchoolUser
from chat.models import Chat


class Message(TimeStampedModel):
    message_id = models.AutoField(primary_key=True, editable=False,
                                  verbose_name="ID сообщения",
                                  help_text="Уникальный идентификатор сообщения")
    user = models.ForeignKey(SchoolUser, on_delete=models.SET_DEFAULT, default=1,
                             verbose_name="Пользователь",
                             help_text="Пользователь, отправивший сообщение")
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='message_chat_id_fk',
                             verbose_name="ID чата",
                             help_text="Чат, в котором было отправлено это сообщение")
    text = models.TextField(max_length=500, verbose_name="Сообщение",
                            help_text="Сообщение, которое было отправлено пользователем")

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
