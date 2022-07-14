import datetime
import os
import random
import re
from users.tasks import send_code
import redis
from django.conf import settings
import secrets
import json


class SenderServiceMixin:
    RUSSIAN_SERVICE_ENDPOINT = "https://smsc.ru/sys/send.php"
    BELARUSIAN_SERVICE_ENDPOINT = "http://app.sms.by/api/v1/sendQuickSMS"
    BY_TOKEN = os.getenv('BY_TOKEN')
    ALFA_SMS = os.getenv("ALFA_SMS")
    RUSSIAN_LOGIN = os.getenv('RUSSIAN_LOGIN')
    RUSSIAN_PASS = os.getenv('RUSSIAN_PASSWORD')
    REDIS_INSTANCE = redis.StrictRedis(host=settings.REDIS_HOST,
                                       port=settings.REDIS_PORT, db=0, password="sOmE_sEcUrE_pAsS")

    def __random_integer_code_generator(self):
        return random.randint(1000, 10000)

    def send_code_by_phone(self, phone: str) -> str | None:
        phone_data = self.check_num(phone)
        if phone_data:
            token = self.save_data_to_redis(phone_data[0])
            if phone_data[1] == "BY":
                params = {
                    "token": SenderServiceMixin.BY_TOKEN,
                    "message": f"https://login/{token}",
                    "phone": phone_data[0],
                    "alphaname_id": SenderServiceMixin.ALFA_SMS,
                }
                send_code.send_code_to_phone.delay(SenderServiceMixin.BELARUSIAN_SERVICE_ENDPOINT,
                                               params,
                                               "post")
            elif phone_data[1] == "RU":
                params = {
                    "login": SenderServiceMixin.RUSSIAN_LOGIN,
                    "psw": SenderServiceMixin.RUSSIAN_PASS,
                    "phones": [phone_data[0]],
                    "mes": f"https://login/{token}",
                    "fmt": 3,
                }
                send_code.send_code_to_phone.delay(SenderServiceMixin.RUSSIAN_SERVICE_ENDPOINT,
                                               params,
                                               "get")
            return phone_data[0]
        else:
            return None

    def send_code_by_email(self, email) -> bool:
        try:
            token = self.save_data_to_redis(email)
            send_code.send_email.delay(email, f"https://login/{token}")
            return True
        except BaseException:
            return False

    def check_num(self, phone_number: str):
        if not phone_number:
            return None
        by = re.compile(r"^(80|375)(25|29|33|44)\d{7}$")
        ru = re.compile(r"^(7)(\d{3})\d{7}$")
        if bool(by.match(phone_number)):
            return phone_number, "BY"
        elif bool(ru.match(phone_number)):
            return phone_number, "RU"
        return None

    def save_data_to_redis(self, recipient: str) -> str:
        token = secrets.token_hex(16)
        SenderServiceMixin.REDIS_INSTANCE.lpush('registration_data',
                                                json.dumps({
                                                    "token": token,
                                                    "recipient": recipient,
                                                    "datetime": datetime.datetime.now().timestamp()
                                                }))
        return token
