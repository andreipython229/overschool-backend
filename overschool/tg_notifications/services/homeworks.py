from ..views import bot, CheckNotification
from time import gmtime
from ..models import TgUsers


class HomeworkNotifications:

    """
        ТГ Уведомления для Менторов и учеников о проверке/отправке заданий
    """

    _last_notifications = {}

    @staticmethod
    def last_notifications(user_homework, last_check_status):

        # Функция для обработки дубликатов при создании домашек

        duplicate = {last_check_status: gmtime()}
        if duplicate in HomeworkNotifications._last_notifications.values():
            return
        else:
            HomeworkNotifications.send_telegram_notification(user_homework, last_check_status)

    @staticmethod
    def send_telegram_notification(user_homework, last_check_status):
        if last_check_status == 'Ждет проверки':
            try:

                # ТГ Уведомления для Менторов

                teacher_id = user_homework.teacher_id
                mentor = TgUsers.objects.get(user_id=teacher_id)

                notifications = CheckNotification.notifications(mentor.id)
                if notifications[mentor.id]['homeworks'] is True:

                    bot.send_message(
                        chat_id=mentor.tg_user_id,
                        text='Ученик прислал работу на проверку! Не забудьте проверить работу ученика на платформе!'
                    )

                    HomeworkNotifications._last_notifications[last_check_status] = {
                        last_check_status: gmtime()
                    }
            except:
                return

        else:
            try:

                # ТГ Уведомления для Учеников

                user_id = user_homework.user_id
                student = TgUsers.objects.get(user_id=user_id)

                notifications = CheckNotification.notifications(student.id)
                if notifications[student.id]['homeworks'] is True:

                    bot.send_message(
                        chat_id=student.tg_user_id,
                        text=f"Ментор проверил ваше задание. Зайдите на платформу для дополнительной информации!"
                    )
            except:
                return
