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
    order = models.IntegerField(
        default=0,
        verbose_name="Порядок отображения чата",
    )

    def __str__(self):
        return f"{self.chat_name} : {self.user_id} (order: {self.order})"

    class Meta:
        verbose_name = "OverAI чат"
        verbose_name_plural = "OverAI чаты"


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

    def __str__(self):
        return str(self.sender) + ": " + str(self.sender_question) + " (" + str(self.message_date) + ")"

    class Meta:
        verbose_name = "Сообщение пользователя"
        verbose_name_plural = "Сообщения пользователей"


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

    def __str__(self):
        return str(self.answer) + "(" + str(self.message_date) + ")"

    class Meta:
        verbose_name = "Ответ нейросети"
        verbose_name_plural = "Ответы нейросети"


class AIProvider(models.Model):
    name = models.CharField(max_length=70)
    provider_type = models.CharField(max_length=40)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Провайдер"
        verbose_name_plural = "Провайдеры"
