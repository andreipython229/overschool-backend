from django.urls import path

import chatgpt.views

urlpatterns = [
    path(
        "send_message/",
        chatgpt.views.SendMessageToGPT.as_view(),
        name="send_message"),
    path(
        "latest_messages/<int:user_id>/",
        chatgpt.views.LastTenMessages.as_view(),
        name="latest_messages"
    ),
]
