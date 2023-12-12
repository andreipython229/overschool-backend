from django.urls import path

import views

urlpatterns = [
    path(
        "send_message/",
        views.send_message_to_gpt,
        name="send_message"),
    path(
        "latest_messages/<int:user_id>/",
        views.latest_messages,
        name="latest_messages"
    ),
]
