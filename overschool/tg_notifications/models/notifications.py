from django.db import models
from .tg_users import TgUsers


class Notifications(models.Model):

    id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID уведомлений для телеграм пользователя",
        help_text="Уникальный идентификатор пользователя",
    )

    homework_notifications = models.BooleanField(
        default=True,
        verbose_name="Уведомления о проверке домашних заданий",
    )

    messages_notifications = models.BooleanField(
        default=True,
        verbose_name="Уведомления о поступлении сообщений с платформы",
    )

    tg_user = models.ForeignKey(
        TgUsers,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Телеграм пользователь",
    )

    def __str__(self):
        return f"уведомления тг пользователя {self.tg_user}"

    class Meta:
        verbose_name = "Телеграм уведомление"
        verbose_name_plural = "Телеграм уведомления"