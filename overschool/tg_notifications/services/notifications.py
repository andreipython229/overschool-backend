from ..models import Notifications


class CheckNotification:

    @staticmethod
    def notifications(user_id):

        """
            Данные из таблицы "tg_notifications_notifications" для проверки вкл/выкл уведомлений
        """

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