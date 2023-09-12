from drf_yasg import openapi

chat_id = {
    "id": "8ecbf7f4-ce05-499a-a73a-21c5acf01c1a",
}
chat = {
    "id": "7f207083-95ab-473f-a9a2-8196413c8097",
    "is_deleted": False,
    "created_at": "2022-10-05T09:36:47.690898Z"
}
chats_list = [{
    "id": "7f207083-95ab-473f-a9a2-8196413c8097",
    "is_deleted": False,
    "created_at": "2022-10-05T09:36:47.690898Z"
}]
messages = [
    {
        "id": 10,
        "sender": 1,
        "sent_at": "2022-10-06T13:35:16.895320Z",
        "content": "new message"
    },
    {
        "id": 11,
        "sender": 2,
        "sent_at": "2022-10-06T13:35:33.305614Z",
        "content": "second message"
    }
]
error_structure = {
    "error": "string",
}


class ChatSchemas:
    chat_uuid_schema = {
        "201": openapi.Response(
            description="CREATED",
            examples={
                "application/json": chat_id
            }
        ),
        "400": openapi.Response(
            description="Bad request",
            examples={
                "application/json": error_structure
            }
        )
    }
    chat_schema = {
        "200": openapi.Response(
            description="OK",
            examples={
                "application/json": chat
            }
        ),
        "400": openapi.Response(
            description="Bad request",
            examples={
                "application/json": error_structure
            }
        )
    }
    chats_for_user_schema = {
        "200": openapi.Response(
            description="OK",
            examples={
                "application/json": chats_list,
            }
        ),
        "400": openapi.Response(
            description="Bad request",
            examples={
                "application/json": error_structure
            }
        )
    }
    messages_schema = {
        "200": openapi.Response(
            description="OK",
            examples={
                "application/json": messages,
            }
        ),
        "400": openapi.Response(
            description="Bad request",
            examples={
                "application/json": error_structure
            }
        )
    }
