import os
import time

import telebot
from db.database import setup_database
from dotenv import load_dotenv
from orm.orm import TgORM
from requests.exceptions import ConnectionError, ReadTimeout
from telebot.apihelper import ApiException

load_dotenv()
bot = telebot.TeleBot(os.environ.get("API_TOKEN"))


@bot.message_handler(commands=["start"])
def cmd_start(message):
    bot.send_message(
        message.from_user.id,
        "Привет, это бот уведомлений платформы OVERSCHOOL. Чтобы продолжить, нужно пройти процедуру верификации. Для этого введите свой адрес эл. почты ниже",
    )


@bot.message_handler(func=lambda message: True)
def get_user(message):
    try:
        user_id = TgORM.select_user_in_db(message.text)
        bot.reply_to(
            message,
            TgORM.insert_user_in_db_tg_users(
                f"{message.from_user.id}", message.from_user.first_name, user_id
            ),
        )
        TgORM.insert_user_in_db_tg_notifications()
    except Exception as e:
        bot.reply_to(
            message,
            f"Произошла ошибка: {str(e)}. Проверьте правильность введенных данных",
        )


def main():
    setup_database()
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except (ReadTimeout, ConnectionError, ApiException) as e:
            print(f"Произошла ошибка: {e}. Повторная попытка через 10 секунд...")
            time.sleep(10)


if __name__ == "__main__":
    main()
