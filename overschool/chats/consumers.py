import json

import jwt
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer
from users.models import User

from .constants import CustomResponses
from .models import Chat, Message, UserChat


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
        message = Message.objects.create(chat=chat, sender=user, content=message)

    def set_room_group_name(self):
        self.room_group_name = f"chat_{self.chat_uuid}"

    async def get_user_id_from_token(self, token):
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        return decoded_token["sub"]

    def get_token_from_headers(self):
        headers = self.scope["headers"]
        token = None
        for head in headers:
            if head[0] == b"cookie":
                cookies = head[1].decode("utf-8")
                cookies_list = cookies.split(";")
                for cookie in cookies_list:
                    if "access_token" in cookie:
                        token = cookie.replace("access_token=", "")
        if token is None:
            raise DenyConnection(CustomResponses.invalid_cookie)
        return token

    async def connect(self):
        self.chat_uuid = self.scope["url_route"]["kwargs"]["room_name"]
        self.chat = await self.is_chat_exist(self.chat_uuid)
        if self.chat is False:
            raise DenyConnection(CustomResponses.chat_not_exist)

        self.token = self.get_token_from_headers()
        print(self.token)
        user_id = await self.get_user_id_from_token(self.token)
        if user_id is None:
            raise DenyConnection(CustomResponses.invalid_cookie)

        try:
            self.user = await sync_to_async(User.objects.get)(id=user_id)
        except User.DoesNotExist:
            raise DenyConnection(CustomResponses.invalid_cookie)
        print(self.user)
        if self.user is None:
            raise DenyConnection(CustomResponses.invalid_cookie)

        user_is_chat_participant = await self.is_chat_participant(self.user, self.chat)
        if user_is_chat_participant is False:
            raise DenyConnection(CustomResponses.no_permission)

        self.set_room_group_name()

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get("message")

        await self.save_message(
            chat=self.chat,
            user=self.user,
            message=message,
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat_message", "message": message, "user": str(self.user)},
        )

    async def chat_message(self, event):
        message = event["message"]
        user = event["user"]

        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "user": user,
                }
            )
        )

    async def disconnect(self, close_code):
        self.set_room_group_name()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
