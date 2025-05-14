import base64
import json
import uuid
from datetime import datetime
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from common_services.selectel_client import UploadToS3
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import F
from users.models import User

from .constants import CustomResponses
from .models import Chat, Message, UserChat

s3 = UploadToS3()
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
    def save_message(self, chat, user, message=None, file_url=None):
        with transaction.atomic():
            UserChat.objects.filter(chat=chat,).exclude(
                user__in=self.connected_users_by_group.get(self.room_group_name, [])
            ).update(unread_messages_count=F("unread_messages_count") + 1)
            message = Message.objects.create(
                chat=chat, sender=user, content=message, file=file_url
            )

        return message.id

    @database_sync_to_async
    def decode_and_upload_file(self, file_data, chat):
        """
        Декодирует файл из Base64, сохраняет его в S3 и возвращает URL.
        """
        # Извлекаем имя файла, тип и содержимое
        file_info = file_data.get("content").split(",")[-1]

        file_content = base64.b64decode(file_info)  # Декодируем содержимое
        file_name = file_data.get("filename", f"file_{uuid.uuid4().hex[:10]}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_file_name = f"{timestamp}_{file_name}"
        file_type = file_data.get("type")

        # Проверяем поддерживаемые типы файлов
        allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/gif"]
        if file_type not in allowed_types:
            raise ValueError("Неподдерживаемый тип файла")

        # Создаем временный файл
        file = ContentFile(file_content, name=unique_file_name)

        # Загружаем файл в S3
        return s3.upload_file_chat(file, f"chats/{chat.id}/")

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

    async def receive(self, text_data=None, bytes_data=None):
        try:

            if text_data:
                # Парсим входные данные
                data = json.loads(text_data)
                message = data.get("message")
                file_data = data.get("file")
                file_url = None

                # Если есть файл, декодируем и загружаем его в S3
                if file_data:
                    try:
                        file_url = await self.decode_and_upload_file(
                            file_data, self.chat
                        )
                    except Exception as e:
                        await self.send(
                            text_data=json.dumps(
                                {"error": f"Ошибка загрузки файла: {str(e)}"}
                            )
                        )
                        return

                # Сохраняем сообщение
                new_message = await self.save_message(
                    chat=self.chat,
                    user=self.user,
                    message=message,
                    file_url=file_url,
                )

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_message",
                        "content": message,
                        "file": file_url,
                        "message_id": new_message,
                        "sender": self.user.id,
                        "id": str(uuid.uuid4()),
                    },
                )
        except ValueError as e:
            # Логируем и возвращаем нормальный текст ошибки
            error_message = str(e)
            await self.send(
                text_data=json.dumps({"error": error_message}, ensure_ascii=False)
            )

    async def chat_message(self, event):
        message = event["content"]
        file = event.get("file")
        user = event["sender"]
        id_key = event["id"]

        file_url = s3.get_link(file) if file else None

        await self.send(
            text_data=json.dumps(
                {
                    "content": message,
                    "file": file_url,
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
        try:
            # Проверяем, существует ли пользователь и группа
            if hasattr(self, "user") and hasattr(self, "room_group_name"):
                self.set_room_group_name()

                # Безопасное удаление пользователя из общего списка
                if hasattr(self, "connected_users"):
                    try:
                        self.connected_users.remove(self.user)
                    except (KeyError, ValueError):
                        pass

                # Отписка от группы channel layer
                try:
                    await self.channel_layer.group_discard(
                        self.room_group_name, self.channel_name
                    )
                except Exception as e:
                    print(f"Error discarding from group: {e}")

                # Безопасное обновление словаря подключенных пользователей
                if (
                    self.room_group_name in self.connected_users_by_group
                    and self.user in self.connected_users_by_group[self.room_group_name]
                ):
                    try:
                        self.connected_users_by_group[self.room_group_name].remove(
                            self.user
                        )

                        # Удаляем группу, только если она пуста
                        if not self.connected_users_by_group[self.room_group_name]:
                            del self.connected_users_by_group[self.room_group_name]
                    except (KeyError, ValueError) as e:
                        print(f"Error updating connected users: {e}")

        except Exception as e:
            print(f"Error in disconnect handler: {e}")
        finally:
            # Всегда вызываем родительский disconnect
            await super().disconnect(close_code)
