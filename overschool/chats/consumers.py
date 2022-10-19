import json

from channels.db import database_sync_to_async
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer

from .constants import CustomResponses
from .models import Chat, UserChat, Message


class ChatConsumer(AsyncWebsocketConsumer):
    @database_sync_to_async
    def is_chat_exist(self, chat_uuid):
        try:
            return Chat.objects.get(id=chat_uuid)
        except Chat.DoesNotExist:
            return False

    @database_sync_to_async
    def is_chat_participant(self, user, chat):
        user_chats = UserChat.objects.filter(chat=chat)
        for user_chat in user_chats:
            if user == user_chat.user:
                return True

        return False

    @database_sync_to_async
    def save_message(self, chat, user, message):
        message = Message.objects.create(
            chat=chat,
            sender=user,
            content=message
        )

    async def connect(self):
        self.chat_uuid = self.scope['url_route']['kwargs']['room_name']
        self.chat = await self.is_chat_exist(self.chat_uuid)
        if self.chat is False:
            raise DenyConnection(CustomResponses.chat_not_exist)

        self.user = self.scope['user']
        user_is_chat_participant = await self.is_chat_participant(self.user, self.chat)
        if user_is_chat_participant is False:
            raise DenyConnection(CustomResponses.no_permission)

        # имя комнаты может содержать только:
        # буквы, цифры, дефисы, символы подчеркивания или точки
        self.room_group_name = f'chat_{self.chat_uuid}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def receive(self, text_data):
        """
        Сервер принимает сообщение от пользователя
        и использует далее указанную функцию (chat_message())
        """
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message')

        await self.save_message(
            chat=self.chat,
            user=self.user,
            message=message,
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                # def chat_message() - функция,
                # которая будет выполняться
                'type': 'chat_message',
                'message': message,
                'user': str(self.user)
            }
        )

    async def chat_message(self, event):
        """
        Сервер рассылает сообщение всем, подключенным к websocket
        """
        message = event['message']
        user = event['user']

        await self.send(text_data=json.dumps({
            'message': message,
            'user': user,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
