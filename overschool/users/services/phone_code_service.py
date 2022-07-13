import os
import random
import re
import users.tasks


class SenderServicePhoneMixin:
    RUSSIAN_SERVICE_ENDPOINT = "https://smsc.ru/sys/send.php"
    BELARUSIAN_SERVICE_ENDPOINT = "http://app.sms.by/api/v1/sendQuickSMS"
    BY_TOKEN = os.getenv('BY_TOKEN')
    ALFA_SMS = os.getenv("ALFA_SMS")
    RUSSIAN_LOGIN = os.getenv('RUSSIAN_LOGIN')
    RUSSIAN_PASS = os.getenv('RUSSIAN_PASSWORD')

    def __random_integer_code_generator(self):
        return random.randint(1000, 10000)

    def sendCode(self, phone: str, date_time: str) -> str | None:
        phone_data = self.check_num(phone)
        if phone_data:
            code = self.__random_integer_code_generator()
            if phone_data[1] == "BY":
                params = {
                    "token": SenderServicePhoneMixin.BY_TOKEN,
                    "message": code,
                    "phone": phone_data[0],
                    "alphaname_id": SenderServicePhoneMixin.ALFA_SMS,
                }
                users.tasks.send_code_to_phone(SenderServicePhoneMixin.BELARUSIAN_SERVICE_ENDPOINT,
                                               params,
                                               "post")
            elif phone_data[1] == "RU":
                params = {
                    "login": SenderServicePhoneMixin.RUSSIAN_LOGIN,
                    "psw": SenderServicePhoneMixin.RUSSIAN_PASS,
                    "phones": [phone_data[0]],
                    "mes": code,
                    "fmt": 3,
                }
                users.tasks.send_code_to_phone(SenderServicePhoneMixin.RUSSIAN_SERVICE_ENDPOINT,
                                               params,
                                               "get")
            return phone_data[0]
        else:
            return None

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
