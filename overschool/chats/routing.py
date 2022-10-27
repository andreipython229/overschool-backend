from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    # (?P<room_name>[0-9a-f-]+) - для uuid
    # (?P<room_name>\w+) - для обычных слов, без тире
    re_path(r'api/chats/(?P<room_name>[0-9a-f-]+)/$', consumers.ChatConsumer.as_asgi()),
]
