from django.urls import path

import chatgpt.views

urlpatterns = [
    path(
        "send_message/",
        chatgpt.views.SendMessageToGPT.as_view(),
        name="send_message"
    ),
    path(
        "latest_messages/<int:user_id>/<int:overai_chat_id>/",
        chatgpt.views.LastTenMessages.as_view(),
        name="latest_messages"
    ),
    path(
        'create_chat/',
         chatgpt.views.CreateChatView.as_view(),
         name='create_chat'
    ),
    path('latest_chats/<int:user_id>/',
         chatgpt.views.LastTenChats.as_view(),
         name='latest_chats'
    ),
    path(
        'delete_chats/<int:user_id>/',
        chatgpt.views.DeleteChatsView.as_view(),
        name='delete_chats'
    ),
    path(
        'user_welcome_message/<int:user_id>/',
        chatgpt.views.UserWelcomeMessageView.as_view(),
        name='user_welcome_message'
    ),
    path(
        'update_welcome_message/<int:user_id>/',
        chatgpt.views.UserWelcomeMessageView.as_view(),
        name='update_welcome_message'),
]
