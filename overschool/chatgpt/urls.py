from django.urls import path

import chatgpt.views

urlpatterns = [
    path(
        "send_message/",
        chatgpt.views.SendMessageToGPT.as_view(),
        name="send_message"
    ),
    path(
        "latest_messages/<int:overai_chat_id>/",
        chatgpt.views.LastMessages.as_view(),
        name="latest_messages"
    ),
    path(
        'create_chat/',
         chatgpt.views.CreateChatView.as_view(),
         name='create_chat'
    ),
    path('latest_chats/',
         chatgpt.views.LastTenChats.as_view(),
         name='latest_chats'
    ),
    path(
        'user_welcome_message/',
        chatgpt.views.UserWelcomeMessageView.as_view(),
        name='user_welcome_message'
    ),
    path(
        'update_welcome_message/',
        chatgpt.views.UserWelcomeMessageView.as_view(),
        name='update_welcome_message'),
    path(
        'delete_chat/',
        chatgpt.views.DeleteChatView.as_view(),
        name='delete_chat'),
    path(
        'assign_chat_order/',
        chatgpt.views.AssignChatOrderView.as_view(),
        name='assign_chat_order'
    ),
]
