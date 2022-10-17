from django.urls import path

from .views import ChatListCreate, ChatDetailDelete, MessageList

urlpatterns = [
    path(
        '',
        ChatListCreate.as_view(),
        name='chats'
    ),
    path(
        '<uuid:chat_uuid>/',
        ChatDetailDelete.as_view(),
        name='chat_detail'
    ),
    path(
        '<uuid:chat_uuid>/messages',
        MessageList.as_view(),
        name='messages'
    ),
]
