import telebot
import os

from rest_framework import viewsets

from .models import Notifications, TgUsers
from .serializers import NotificationsSerializer

bot_token = os.environ.get('TG_BOT_TOKEN')
bot = telebot.TeleBot(bot_token)


class BotNotifications:

    @staticmethod
    def send_notifications(tg_user_id, notifications):
        bot.send_message(
            chat_id=tg_user_id,
            text=notifications
        )


class NotificationsViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationsSerializer

    def get_queryset(self, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return (
                TgUsers.objects.none()
            )
        user = self.request.user
        queryset = Notifications.objects.filter(tg_user_id__user_id=user)
        return queryset

    class Meta:
        model = Notifications
