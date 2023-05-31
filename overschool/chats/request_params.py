from drf_yasg import openapi


class UserParams:
    user_id = openapi.Parameter(
        "user_id",
        openapi.IN_FORM,
        description="The user to start a chat with",
        type=openapi.TYPE_INTEGER,
        required=True
    )


class ChatParams:
    uuid = openapi.Parameter(
        "chat_uuid",
        openapi.IN_PATH,
        description="Chat UUID",
        type=openapi.TYPE_STRING,
        required=True
    )
