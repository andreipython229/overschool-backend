from django.urls import path

import chatgpt.views

urlpatterns = [
    path(
        "send_message/",
        chatgpt.views.send_message_to_gpt,
        name="send_message"),
    path(
        "latest_messages/<int:user_id>/",
        chatgpt.views.last_10_messages,
        name="latest_messages"
    ),
]
