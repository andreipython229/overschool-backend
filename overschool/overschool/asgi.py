import datetime
import logging
import os
import time
from channels.auth import AuthMiddlewareStack
import sentry_sdk
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import SentryHandler

# Настройки Sentry
SENTRY_INIT_OPTIONS = {
    "dsn": "https://84b3a15795cd47f5a01a552151dabc06@o4505167864463360.ingest.sentry.io/4505173034270720",
    "integrations": [DjangoIntegration()],
    "send_default_pii": True,
}
sentry_sdk.init(**SENTRY_INIT_OPTIONS)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = SentryHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

logger.addHandler(handler)

message = "Сервер успешно запущен!"
timestamp = time.time() + 10800
formatted_time = datetime.datetime.fromtimestamp(timestamp).strftime(
    "%d-%m-%Y -> %H:%M"
)
formatted_message = "{} (время записи: {})".format(message, formatted_time)
logger.info(formatted_message)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "overschool.settings")
django_asgi_app = get_asgi_application()

import chats.routing


application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(chats.routing.websocket_urlpatterns))
        ),
    }
)

