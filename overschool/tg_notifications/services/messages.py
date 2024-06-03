from ..models import TgUsers
from ..views import BotNotifications
from .notifications import CheckNotification
from users.models import User
from chats.models import Message
from datetime import timedelta


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

                    # Находим участника/ов чата

                    tg_user = TgUsers.objects.get(user_id=user.id)

                    # проверка на уведомления

                    notifications = CheckNotification.notifications(tg_user.id)
                    if notifications.get(tg_user.id, {}).get('messages', False):

                        try:

                            # Перед отправкой уведомления проверяется,
                            # прошло ли более 10 минут с момента последнего отправленного
                            # сообщения от этого же отправителя в нужный чат

                            last_message = Message.objects.filter(
                                chat_id=data.chat_id,
                                sender_id=data.sender.id,
                                sent_at__lt=data.sent_at
                            ).latest('sent_at')

                            if last_message and (data.sent_at - last_message.sent_at) < timedelta(minutes=10):
                                continue
                        except Message.DoesNotExist:
                            pass

                        text = f"Вам пришло от пользователя {sender.last_name} {sender.first_name}\
                                сообщение в чате:\n{data.content}\nЗайдите на платформу для дополнительной информации!"

                        BotNotifications.send_notifications(tg_user.tg_user_id, text)

            except:
                return
