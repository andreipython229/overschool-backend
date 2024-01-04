from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

send_message_schema = swagger_auto_schema(
    operation_description="Эндпоинт для отправки сообщения.\n"
                         "Может использоваться любым пользователем.",
    operation_summary="Эндпоинт отправки сообщения",
    tags=["chatgpt"],
)

latest_messages_schema = swagger_auto_schema(
    operation_description="Эндпоинт для получения последних десяти сообщений пользователя.\n"
                         "Может использоваться любой пользователь.",
    operation_summary="Эндпоинт последних сообщений",
    tags=["chatgpt"],
)
