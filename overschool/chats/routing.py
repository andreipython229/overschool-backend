from django.urls import re_path

from . import consumers
from overschool.consumers import InfoConsumers

websocket_urlpatterns = [
    # (?P<room_name>[0-9a-f-]+) - для uuid
    # (?P<room_name>\w+) - для обычных слов, без тире
    re_path(r'ws/chats/(?P<room_name>[0-9a-f-]+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/info/(?P<school_name>[\w\s-]+)/$', InfoConsumers.as_asgi()),

]
