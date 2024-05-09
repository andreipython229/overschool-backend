import telebot
import os
from .models import Notifications

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
        except Exception as e:
            print(e)