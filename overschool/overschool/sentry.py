import datetime
import logging
import time

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import SentryHandler

SENTRY_INIT_OPTIONS = {
    'dsn': 'https://84b3a15795cd47f5a01a552151dabc06@o4505167864463360.ingest.sentry.io/4505173034270720',
    'integrations': [
        DjangoIntegration(
            transaction_style='url',
            middleware_spans=True,

        ),
    ],
    'send_default_pii': True,
}

sentry_sdk.init(**SENTRY_INIT_OPTIONS)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = SentryHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger.addHandler(handler)

message = 'Сервер успешно запущен!'
timestamp = time.time() + 10800
formatted_time = datetime.datetime.fromtimestamp(timestamp).strftime('%d-%m-%Y -> %H:%M')
formatted_message = '{} (время записи: {})'.format(message, formatted_time)
logger.info(formatted_message)
