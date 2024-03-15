import json

import jwt
from channels.db import database_sync_to_async
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer
from chats.models import UserChat
from chats.services import get_chats_info_async, get_unread_appeals_count
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q, Sum
from schools.models import School
from users.models import User


class InfoConsumers(AsyncWebsocketConsumer):
    connected_users = []

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
            raise DenyConnection({"error": "token error"})
        return token

    @database_sync_to_async
    def get_total_unread_count(self, user):
        unread_count = UserChat.objects.filter(
            user=user, chat__is_deleted=False
        ).aggregate(total_unread=Sum("unread_messages_count"))["total_unread"]
        return unread_count

    async def connect(self):
        self.token = self.get_token_from_headers()
        user_id = await self.get_user_id_from_token(self.token)
        if user_id is None:
            raise DenyConnection({"error": "user_id is None"})

        try:
            self.user = await database_sync_to_async(User.objects.get)(id=user_id)
        except User.DoesNotExist:
            raise DenyConnection({"error": "User.DoesNotExist"})
        if self.user is None:
            raise DenyConnection({"error": "self.user is None"})

        self.group_name = f"user_{user_id}_group"
        if self.user is not None and self.user in self.connected_users:
            # print("Юзер уже подключён")
            self.connected_users.remove(self.user)
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            # raise DenyConnection({"error":"Юзер уже подключён"})

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        self.connected_users.append(self.user)
        await self.accept()

        # print("connected users: ", self.connected_users)

        # total_unread = await self.get_total_unread_count(self.user)
        #
        # if total_unread:
        #     await self.send(
        #         text_data=json.dumps(
        #             {
        #                 "type": "short_chat_info",
        #                 "message": {
        #                     "total_unread": total_unread,
        #                     "chats": []
        #                 }
        #             },
        #             cls=DjangoJSONEncoder,
        #         )
        #     )
        # Получаем роли пользователя
        school_name = self.scope["url_route"]["kwargs"].get("school_name")
        try:
            school = await database_sync_to_async(School.objects.get)(name=school_name)
            is_admin = await database_sync_to_async(
                self.user.groups.filter(
                    Q(group__name="Admin") & Q(school=school.school_id)
                ).exists
            )()

            if is_admin:
                unread_appeals_count = await get_unread_appeals_count(school)

                # Отправляем количество непрочитанных заявок через WebSocket
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "unread_appeals_count",
                            "school_id": school.school_id,
                            "unread_count": unread_appeals_count,
                        }
                    )
                )
        except School.DoesNotExist:
            print(f"Школа с именем '{school_name}' не найдена.")
        message = await get_chats_info_async(self.user)
        await self.send(
            text_data=json.dumps({"type": "full_chat_info", "message": message})
        )

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            self.connected_users.remove(self.user)
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            # print("connected_users: ", self.connected_users)
        else:
            print("No group_name")

    async def receive(self, text_data):
        data_json = json.loads(text_data)
        message = data_json["message"]
        target_employee_id = data_json["target_user_id"]

        target_group_name = f"user_{target_employee_id}_group"

        if target_group_name == self.group_name:
            await self.send(text_data=json.dumps({"message": message}))

    async def user_inform(self, event):
        user_id = event["user_id"]
        target_group_name = f"user_{user_id}_group"

        if target_group_name == self.group_name:
            await self.send(
                text_data=json.dumps(
                    {"type": "full_chat_info", "message": event["message"]}
                )
            )

    async def unread_appeals_count(self, event):
        school_id = event["school_id"]
        unread_count = event["unread_count"]

        # Проверяем, что школа пользователя совпадает с школой, для которой предназначено событие
        if self.user.groups.filter(school=school_id).exists():
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "unread_appeals_count",
                        "school_id": school_id,
                        "unread_count": unread_count,
                    }
                )
            )
