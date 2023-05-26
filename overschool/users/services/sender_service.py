from __future__ import annotations

import os
import random
import re

import redis
from django.conf import settings

from users.tasks import send_code

from .redis_data_mixin import RedisDataMixin


import random
import re



class SenderServiceMixin(RedisDataMixin):
    """Функционал для отправки регистрационных сообщений ученикам, менеджерам"""

    RUSSIAN_SERVICE_ENDPOINT = "https://smsc.ru/sys/send.php"
    BELARUSIAN_SERVICE_ENDPOINT = "http://app.sms.by/api/v1/sendQuickSMS"
    BY_TOKEN = os.getenv("BY_TOKEN")
    ALFA_SMS = os.getenv("ALFA_SMS")
    RUSSIAN_LOGIN = os.getenv("RUSSIAN_LOGIN")
    RUSSIAN_PASS = os.getenv("RUSSIAN_PASSWORD")
    REDIS_INSTANCE = redis.StrictRedis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        password="sOmE_sEcUrE_pAsS",
    )

    def generate_confirmation_code(self) -> str:
        """
        Генерация кода подтверждения из 4 цифр
        """
        code = random.randint(1000, 9999)
        return str(code)

    def send_code_by_phone(self, phone: str, user_type: int, group: int = 0, course: int = 0) -> str | None:
        """
        Отправка кода на телефон, пока поддерживаются только белорусские и русские номера
        """
        phone_data = self.check_num(phone)
        if phone_data:
            token = self._save_data_to_redis(phone_data[0], user_type, course, group)
            confirmation_code = self.generate_confirmation_code()
            if phone_data[1] == "BY":
                params = {
                    "token": SenderServiceMixin.BY_TOKEN,
                    "message": f"Код подтверждения: {confirmation_code}",
                    "phone": phone_data[0],
                    "alphaname_id": SenderServiceMixin.ALFA_SMS,
                }
                send_code.send_code_to_phone.delay(
                    SenderServiceMixin.BELARUSIAN_SERVICE_ENDPOINT, params, "post"
                )
            elif phone_data[1] == "RU":
                params = {
                    "login": SenderServiceMixin.RUSSIAN_LOGIN,
                    "psw": SenderServiceMixin.RUSSIAN_PASS,
                    "phones": [phone_data[0]],
                    "mes": f"Код подтверждения: {confirmation_code}",
                    "fmt": 3,
                }
                send_code.send_code_to_phone.delay(
                    SenderServiceMixin.RUSSIAN_SERVICE_ENDPOINT, params, "get"
                )
            return confirmation_code
        else:
            return None

   

    def check_num(self, phone_number: str):
        """
        Приведение номера в нормальный вид
        """
        if not phone_number:
            return None
        by = re.compile(r"^(80|375)(25|29|33|44)\d{7}$")
        ru = re.compile(r"^(7)(\d{3})\d{7}$")
        if bool(by.match(phone_number)):
            return phone_number, "BY"
        elif bool(ru.match(phone_number)):
            return phone_number, "RU"
        return None