from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class OverAiChatSchemas:
    @staticmethod
    def create_chat_schema():
        return swagger_auto_schema(
            tags=["over ai"],
            operation_description="Создать новый чат OverAI",
            operation_summary="Создать новый чат OverAI",
        )

    @staticmethod
    def delete_chats_schema():
        return swagger_auto_schema(
            tags=["over ai"],
            operation_description="Удалить пустые чаты пользователя",
            operation_summary="Удалить пустые чаты пользователя",
        )


class LastMessagesSchema:
    @staticmethod
    def last_messages_get_schema():
        return swagger_auto_schema(
            tags=["over ai"],
            operation_description="Получить последние сообщения чата с OVER AI",
            operation_summary="Получить последние сообщения чата с OVER AI",
            responses={200: 'Успешный запрос', 500: 'Ошибка сервера'},
        )


class SendMessageToGPTSchema:
    @staticmethod
    def send_message_schema():
        return swagger_auto_schema(
            tags=["over ai"],
            request_body=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Сообщение от пользователя'),
                    'overai_chat_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID чата OverAI')
                }
            ),
            operation_description="Отправить сообщение в OVER AI",
            operation_summary="Отправить сообщение в OVER AI",
            responses={200: 'Успешный запрос', 500: 'Ошибка сервера'},
        )


class LastTenChatsSchema:
    @staticmethod
    def last_ten_chats_get_schema():
        return swagger_auto_schema(
            tags=["over ai"],
            operation_description="Получить последние 10 чатов пользователя",
            operation_summary="Получить последние 10 чатов пользователя",
            responses={200: 'Успешный запрос', 500: 'Ошибка сервера'},
        )

