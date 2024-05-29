from ..models import TgUsers
from ..views import bot, CheckNotification
from users.models import User


class MessagesNotifications:

    """
        ТГ Уведомления для Всех  о непрочитанных сообщениях в чате
    """

    @staticmethod
    def send_messages_notifications(users, data):
        for user in users:
            try:
                if user.id != data.sender.id:

                    # Находим отправителя сообщения
                    sender = User.objects.get(id=data.sender.id)

                    tg_user = TgUsers.objects.get(user_id=user.id)

                    # проверка на уведомления
                    notifications = CheckNotification.notifications(tg_user.id)
                    if notifications[tg_user.id]['messages'] is True:

                        bot.send_message(
                            chat_id=tg_user.tg_user_id,
                            text=f"Вам пришло от пользователя {sender.first_name} {sender.last_name}\
                            сообщение:\n{data.content}\nЗайдите на платформу для дополнительной информации!"
                        )
            except:
                return
