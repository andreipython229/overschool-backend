from django.db import models

from common_services.mixins import TimeStampMixin
from users.models import User


class Chat(TimeStampMixin, models.Model):
    """
    Модель чата
    """

    chat_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID чата",
        help_text="Уникальный идентификатор чата",
    )
    admin = models.ForeignKey(
        User,
        on_delete=models.SET_DEFAULT,
        default=1,
        verbose_name="Админ",
        help_text="Пользователь, являющийся админом чата, по умолчанию - супер админ",
    )
    participants = models.ManyToManyField(
        User, related_name="user_chat_mtm", verbose_name="Пользователи"
    )

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"
