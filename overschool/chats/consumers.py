import json
import uuid
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import F
from users.models import User

from .constants import CustomResponses
from .models import Chat, Message, UserChat

channel_layer = get_channel_layer()


class ChatConsumer(AsyncWebsocketConsumer):
    connected_users = []
    message_history = {}
    connected_users_by_group = {}

    @database_sync_to_async
    def is_chat_exist(self, chat_uuid):
        try:
            return Chat.objects.get(id=chat_uuid)
        except Chat.DoesNotExist:
            return False

    @database_sync_to_async
    def is_chat_participant(self, user, chat):
        user_chats = UserChat.objects.filter(chat=chat, user=user)
        return user_chats.exists()

    @database_sync_to_async
    def save_message(self, chat, user, message):
        with transaction.atomic():
            UserChat.objects.filter(chat=chat,).exclude(
                user__in=self.connected_users_by_group.get(self.room_group_name, [])
            ).update(unread_messages_count=F("unread_messages_count") + 1)
            message = Message.objects.create(chat=chat, sender=user, content=message)

        return message.id

    @database_sync_to_async
    def get_chat_messages(self, chat):
        return Message.objects.filter(chat=chat)

    def set_room_group_name(self):
        self.room_group_name = f"chat_{self.chat_uuid}"

    async def connect(self):
        self.chat_uuid = self.scope["url_route"]["kwargs"]["room_name"]
        self.chat = await self.is_chat_exist(self.chat_uuid)
        if self.chat is False:
            raise DenyConnection(CustomResponses.chat_not_exist)

        query_string = self.scope["query_string"].decode()
        query_params = parse_qs(query_string)

        # Получаем user_id из параметров запроса
        user_id = query_params.get("user_id", [None])[0]
        print("user_id: ", user_id)
        if user_id is None:
            raise DenyConnection(CustomResponses.invalid_cookie)

        try:
            self.user = await database_sync_to_async(User.objects.get)(id=user_id)
        except User.DoesNotExist:
            raise DenyConnection(CustomResponses.invalid_cookie)
        if self.user is None:
            raise DenyConnection(CustomResponses.invalid_cookie)

        await self.is_chat_participant(self.user, self.chat)
        # if user_is_chat_participant:
        #     history = self.message_history.get(self.chat.id, [])
        #     await self.send(
        #         text_data=json.dumps(
        #             {"type": "chat_history", "history": history},
        #             cls=DjangoJSONEncoder,
        #         )
        #     )
        # else:
        #     raise DenyConnection(CustomResponses.no_permission)

        self.connected_users.append(self.user)
        self.set_room_group_name()

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Обновляем словарь подключенных пользователей
        if self.room_group_name not in self.connected_users_by_group:
            self.connected_users_by_group[self.room_group_name] = []
        self.connected_users_by_group[self.room_group_name].append(self.user)
        # print("CONNECTED USERS BY GROUP: ", self.connected_users_by_group)

        # Сбрасываем счетчик непрочитанных сообщений для данного пользователя и чата
        try:
            user_chat = await database_sync_to_async(UserChat.objects.get)(
                user=self.user, chat=self.chat
            )
            if user_chat.unread_messages_count > 0:
                user_chat.unread_messages_count = 0
                await database_sync_to_async(user_chat.save)()
        except:
            raise DenyConnection({"error": "user_chat error"})

        await self.accept()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get("message")
        new_message = await self.save_message(
            chat=self.chat,
            user=self.user,
            message=message,
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "content": message,
                "message_id": new_message,
                "sender": self.user.id,
                "id": str(uuid.uuid4()),
            },
        )

    async def chat_message(self, event):
        message = event["content"]
        user = event["sender"]
        id_key = event["id"]
        event["message_id"]

        await self.send(
            text_data=json.dumps(
                {
                    "content": message,
                    "sender": user,
                    "id": id_key,
                }
            )
        )

    async def chat_created(self, event):
        chat_id = event["chat_id"]
        group_id = event["group_id"]
        group_name = event["group_name"]

        # Отправляем информацию о созданном чате клиенту
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_created",
                    "chat_id": chat_id,
                    "group_id": group_id,
                    "group_name": group_name,
                }
            )
        )

    async def disconnect(self, close_code):
        self.set_room_group_name()
        self.connected_users.remove(self.user)
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # Обновляем словарь подключенных пользователей
        if self.room_group_name in self.connected_users_by_group:
            self.connected_users_by_group[self.room_group_name].remove(self.user)
            if len(self.connected_users_by_group[self.room_group_name]) == 0:
                del self.connected_users_by_group[self.room_group_name]
            # print("CONNECTED USERS BY GROUP: ", self.connected_users_by_group)
