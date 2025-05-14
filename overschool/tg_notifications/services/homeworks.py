from ..api_views.bot import BotNotifications
from .notifications import CheckNotification
from ..models import TgUsers


class HomeworkNotifications:

    """
        ТГ Уведомления для Менторов и учеников о проверке/отправке заданий
    """

    _notification_for_mentor = 'Ученик прислал работу на проверку! Не забудьте проверить работу ученика на платформе!'
    _notification_for_student = 'Ментор проверил ваше задание. Зайдите на платформу для дополнительной информации!'

    @staticmethod
    def send_telegram_notification(user_homework, data):
        try:
            if data.status == 'Ждет проверки':

                # ТГ Уведомления для Менторов

                mentor = TgUsers.objects.get(user_id=user_homework.teacher_id)

                notifications = CheckNotification.notifications(mentor.id)
                if notifications.get(mentor.id, {}).get('homeworks', False):
                    BotNotifications.send_notifications(
                        mentor.tg_user_id,
                        HomeworkNotifications._notification_for_mentor
                    )
            #
            else:

                # ТГ Уведомления для Учеников

                student = TgUsers.objects.get(user_id=user_homework.user_id)

                notifications = CheckNotification.notifications(student.id)
                if notifications.get(student.id, {}).get('homeworks', False):
                    BotNotifications.send_notifications(
                        student.tg_user_id,
                        HomeworkNotifications._notification_for_student
                    )
        except:
            return

