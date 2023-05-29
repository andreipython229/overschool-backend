import datetime
import json
import secrets

import redis
from django.conf import settings


class RedisDataMixin:
    """Функционал для работы с базой redis"""

    REDIS_INSTANCE = redis.StrictRedis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        password="sOmE_sEcUrE_pAsS",
    )
    REGISTRATION_DATA_KEY = "registration_data"

    def _get_data_token(self, token: str) -> dict:
        """
        Функция для получения данных по токену
        """
        for i in range(
                0, RedisDataMixin.REDIS_INSTANCE.llen(RedisDataMixin.REGISTRATION_DATA_KEY)
        ):
            record = RedisDataMixin.REDIS_INSTANCE.lindex(
                RedisDataMixin.REGISTRATION_DATA_KEY, i
            )
            record_loads = json.loads(record)
            if record_loads["token"] == token:
                data = record_loads
                break
        else:
            data = {}
        return data

    def _save_data_to_redis(self, recipient: str, user_type: int, group: int = 0, course: int = 0, ) -> str:
        """
        Функция сохранения данных для регистрации, пока в redis (есть идея сохранять в бд)
        """
        token = secrets.token_hex(16)
        RedisDataMixin.REDIS_INSTANCE.lpush(
            RedisDataMixin.REGISTRATION_DATA_KEY,
            json.dumps(
                {
                    "token": token,
                    "recipient": recipient,
                    "user_type": user_type,
                    "course": course,
                    "group": group,
                    "status": True,
                    "datetime": datetime.datetime.now().timestamp(),
                }
            ),
        )
        return token

    def _delete_data_from_redis(self, token):
        for i in range(
                0, RedisDataMixin.REDIS_INSTANCE.llen(RedisDataMixin.REGISTRATION_DATA_KEY)
        ):
            record = RedisDataMixin.REDIS_INSTANCE.lindex(
                RedisDataMixin.REGISTRATION_DATA_KEY, i
            )
            record_loads = json.loads(record)
            if record_loads["token"] == token:
                data = record_loads
                break
        else:
            data = {}
        return data

    def save_reset_code(self, email_or_phone, reset_code):
        """
        Сохраняет код для сброса пароля в Redis или другое хранилище
        """
        # Сохраняем код для сброса пароля в Redis
        key = f"reset_code:{email_or_phone}"
        RedisDataMixin.REDIS_INSTANCE.set(key, reset_code)
        # Дополнительно можно установить время жизни ключа, например, на 24 часа
        RedisDataMixin.REDIS_INSTANCE.expire(key, 24 * 60 * 60)
