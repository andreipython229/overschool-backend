from __future__ import annotations

import os
import random
import re

import redis
from django.conf import settings
from users.tasks import send_code

from .redis_data_mixin import RedisDataMixin


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

    def get_data_token(self, token):
        """
        Используется для получения всей необходимой информации
        """

    def __random_integer_code_generator(self):
        """
        Хотел использовать для генерации кода, но мне не понадобилось, может кому-то надо будет
        """
        return random.randint(1000, 10000)

    def send_code_by_phone(self, phone: str, user_type: int, course: int = 0) -> str | None:
        """
        Отправка кода на телефон, пока поддерживаются только белорусские и русские номера
        """
        phone_data = self.check_num(phone)
        if phone_data:
            token = self._save_data_to_redis(phone_data[0], user_type, course)
            if phone_data[1] == "BY":
                params = {
                    "token": SenderServiceMixin.BY_TOKEN,
                    "message": f"https://overschool/users/login/?token={token}",
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
                    "mes": f"https://overschool/users/login/?token={token}",
                    "fmt": 3,
                }
                send_code.send_code_to_phone.delay(
                    SenderServiceMixin.RUSSIAN_SERVICE_ENDPOINT, params, "get"
                )
            return phone_data[0]
        else:
            return None

    def send_code_by_email(self, email: str, user_type: int, course: int = 0) -> bool:
        """
        Отправка ссылки на email
        """
        try:
            token = self._save_data_to_redis(email, user_type, course)
            send_code.send_email.delay(
                email, f"https://overschool/users/login/?token={token}"
            )
            return True
        except BaseException:
            return False

    def check_num(self, phone_number: str):
        """
        Приведения номера в нормальный вид
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
