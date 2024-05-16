from ..views import bot, CheckNotification
from time import gmtime
from ..models import TgUsers


class HomeworkNotifications:
    _last_notifications = {}

    @staticmethod
    def last_notifications(user_homework, last_check_status, last_check_mark):

        """
            Функция для обработки дубликатов при создании домашек
        """

        duplicate = {last_check_status: gmtime()}
        if duplicate in HomeworkNotifications._last_notifications.values():
            return
        else:
            HomeworkNotifications.send_telegram_notification(user_homework, last_check_status, last_check_mark)

    @staticmethod
    def send_telegram_notification(user_homework, last_check_status, last_check_mark):
        if last_check_status == 'Ждет проверки':
            try:
                teacher_id = user_homework.teacher_id
                mentor = TgUsers.objects.get(user_id=teacher_id)

                notifications = CheckNotification.notifications(mentor.id)
                if notifications[mentor.id]['homeworks'] is True:

                    bot.send_message(
                        chat_id=mentor.tg_user_id,
                        text='Ученик прислал работу на проверку! Не забудьте проверить работу ученика на платформе!'
                    )
                    print('сообщение отправлено ментору')

                    HomeworkNotifications._last_notifications[last_check_status] = {
                        last_check_status: gmtime()
                    }
                else:
                    print('Ментор не включил уведомления о присланных дз')
            except:
                print('Ментор не включил уведомления')

        else:
            try:
                user_id = user_homework.user_id
                student = TgUsers.objects.get(user_id=user_id)

                notifications = CheckNotification.notifications(student.id)
                if notifications[student.id]['homeworks'] is True:

                    bot.send_message(
                        chat_id=student.tg_user_id,
                        text=f"Ментор проверил ваше задание. Зайдите на платформу для дополнительной информации!"
                    )
                    print('сообщение отправлено студенту')
                else:
                    print('Студент не включил уведомления о проверенных дз')

            except:
                print('Студент не включил уведомления')
