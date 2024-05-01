from orm.orm import TgORM
import os
import telebot
from dotenv import load_dotenv
from db.database import setup_database

bot = telebot.TeleBot(os.environ.get('API_TOKEN'))


@bot.message_handler(commands=['start'])
def cmd_start(message):
    bot.send_message(
        message.from_user.id,
        'Привет, это бот уведомлений платформы OVERSCHOOL. Чтобы продолжить, нужно пройти процедуру верификации. Для этого введите свой адрес эл. почты ниже'
    )


@bot.message_handler(func=lambda message: True)
def get_user(message):
    try:
        user_id = TgORM.select_user_in_db(message.text)
        bot.reply_to(message,
                     TgORM.insert_user_in_db_tg_users(
                         f'{message.from_user.id}',
                         message.from_user.first_name,
                         user_id
                     ),
                     )
        TgORM.insert_user_in_db_tg_notifications()
    except Exception:
        bot.reply_to(message, "Проверьте правильность введенных данных")


load_dotenv()


def main():
    setup_database()
    bot.infinity_polling()


"""
    Перед запуском бота, подгрузить зависимости из requirements.txt!
"""
if __name__ == "__main__":
    main()