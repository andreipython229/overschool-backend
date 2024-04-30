import json
import os
import telebot

from .models import TgUsers, Notifications

bot_token = os.environ.get('TG_BOT_TOKEN')
bot = telebot.TeleBot(bot_token)


class SendNotifications:
    _last_notifications = []

    @staticmethod
    def last_notifications(user_homework, last_check_status, last_check_mark):
        try:
            if last_check_status == SendNotifications._last_notifications[-1]:
                return
            else:
                SendNotifications.send_telegram_notification(user_homework, last_check_status, last_check_mark)
        except Exception:
            SendNotifications.send_telegram_notification(user_homework, last_check_status, last_check_mark)

    @staticmethod
    def send_telegram_notification(user_homework, last_check_status, last_check_mark):
        if last_check_status == 'Ждет проверки':
            try:
                query = TgUsers.objects.filter(user_id=user_homework.teacher_id)

                mentor = {
                    mentor.user_id: {
                        'tg_user_id': mentor.tg_user_id,
                        'first_name': mentor.first_name
                    } for mentor in query
                }

                mentor_chat_id = mentor[user_homework.teacher_id]['tg_user_id']

                bot.send_message(
                    chat_id=mentor_chat_id,
                    text='Ученик прислал работу на проверку! Не забудьте проверить работу учеников на платформе!'
                )
                print('сообщение отправлено ментору')

                SendNotifications._last_notifications.append(last_check_status)
            except Exception as e:
                return f"{e}"
        else:
            try:
                query = TgUsers.objects.filter(user_id=user_homework.user_id)

                student = {
                    student.user_id: {
                        'tg_user_id': student.tg_user_id,
                        'first_name': student.first_name
                    } for student in query
                }

                student_chat_id = student[user_homework.user_id]['tg_user_id']
                number_hw = user_homework.text

                bot.send_message(
                    chat_id=student_chat_id,
                    text=f"Ваше задание '{number_hw}' {last_check_status.lower()}, с отметкой {last_check_mark}"
                )
                print('сообщение отправлено студенту')

                SendNotifications._last_notifications.append(last_check_status)
            except Exception as e:
                return f"{e}"
