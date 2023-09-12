from django.urls import path

from .views import ChatDetailDelete, ChatListCreate, MessageList

urlpatterns = [
    path(
        "", ChatListCreate.as_view(actions={"get": "get", "post": "post"}), name="chats"
    ),
    path(
        "<uuid:chat_uuid>/",
        ChatDetailDelete.as_view(actions={"get": "get", "patch": "patch"}),
        name="chat_detail",
    ),
    path(
        "<uuid:chat_uuid>/messages",
        MessageList.as_view(actions={"get": "get"}),
        name="messages",
    ),
]
