import telebot
import os

from rest_framework.response import Response
from rest_framework import viewsets, status
from .models import Notifications, TgUsers
from .serializers import NotificationsSerializer

bot_token = os.environ.get('TG_BOT_TOKEN')
bot = telebot.TeleBot(bot_token)


class CheckNotification:

    @staticmethod
    def notifications(user_id):
        try:
            query = Notifications.objects.filter(tg_user_id=user_id)

            notifications = {
                notifications.tg_user_id: {
                    'messages': notifications.messages_notifications,
                    'homeworks': notifications.homework_notifications,
                    'completed_courses': notifications.completed_courses_notifications,
                } for notifications in query
            }

            return notifications
        except:
            return


class NotificationsViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationsSerializer

    def get_queryset(self, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return (
                TgUsers.objects.none()
            )
        user = self.request.user
        queryset = (Notifications.objects.filter(tg_user_id__user_id=user))
        return queryset

    class Meta:
        model = Notifications
