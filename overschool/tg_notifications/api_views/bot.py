import telebot
import os


bot_token = os.environ.get('TG_BOT_TOKEN')
bot = telebot.TeleBot(bot_token)


class BotNotifications:

    @staticmethod
    def send_notifications(tg_user_id, notifications):
        bot.send_message(
            chat_id=tg_user_id,
            text=notifications
        )
