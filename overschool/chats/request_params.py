from drf_yasg import openapi


class UserParams:
    user_id = openapi.Parameter(
        "user_id",
        openapi.IN_FORM,
        description="The user to start a chat with",
        type=openapi.TYPE_INTEGER,
        required=True
    )
    name = openapi.Parameter(
        "role_name",
        openapi.IN_FORM,
        description="Role name",
        type=openapi.TYPE_STRING
    )


class ChatParams:
    uuid = openapi.Parameter(
        "chat_uuid",
        openapi.IN_PATH,
        description="Chat UUID",
        type=openapi.TYPE_STRING,
        required=True
    )
    name = openapi.Parameter(
        "name",
        openapi.IN_FORM,
        description="Chat name",
        type=openapi.TYPE_STRING
    )
    is_deleted = openapi.Parameter(
        "is_deleted",
        openapi.IN_FORM,
        description="Delete or restore chat",
        type=openapi.TYPE_BOOLEAN
    )
