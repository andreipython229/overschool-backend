from django.urls import path

from .views import ChatDetailDelete, ChatListCreate, MessageList, create_or_update_group_chat

urlpatterns = [
    path(
        "", ChatListCreate.as_view(actions={"get": "get", "post": "post"}), name="chats"
    ),
    path(
        "<uuid:chat_uuid>/",
        ChatDetailDelete.as_view(
            actions={"get": "get", "patch": "patch", "delete": "delete"}
        ),
        name="chat_detail",
    ),
    path(
        "<uuid:chat_uuid>/messages",
        MessageList.as_view(actions={"get": "get"}),
        name="messages",
    ),
    path(
        "create_personal_chat/",
        ChatListCreate.as_view(actions={"post": "create_personal_chat"}),
        name="create_personal_chat",
    ),
    path('chat_synchronizer/<int:group_id>/',
         create_or_update_group_chat,
         name='create_or_update_group_chat'
    ),
]
