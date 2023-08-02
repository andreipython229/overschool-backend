from __future__ import annotations

import os
import random
from typing import Optional

import redis
from django.conf import settings
from django.core.mail import send_mail
from users.models import User

from .redis_data_mixin import RedisDataMixin


class SenderServiceMixin(RedisDataMixin):
    """Functionalities for sending registration messages to students and managers"""

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
        Generate a 4-digit confirmation code
        """
        code = random.randint(1000, 9999)
        return str(code)

    def save_confirmation_code(self, email: str, confirmation_code: str):
        """
        Save the confirmation code in the user's confirmation_code field
        """
        user = User.objects.filter(email=email).first()
        if user:
            user.confirmation_code = confirmation_code
            user.save()

    def send_code_by_email(self, email: str) -> Optional[str]:
        """
        Send code by email
        """
        confirmation_code = self.generate_confirmation_code()
        self.save_confirmation_code(email, confirmation_code)

        # Send the confirmation code via email
        subject = "Confirmation Code"
        message = f"Your confirmation code is: {confirmation_code}"
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]

        try:
            send_mail(subject, message, from_email, recipient_list)
        except Exception as e:
            # Handle the error or raise an exception
            print(f"Failed to send email: {e}")

        return confirmation_code

    # def send_code_by_phone(self, phone_number: str, user: User) -> Optional[str]:
    #     """
    #     Send code to a phone number (currently supports Belarusian and Russian numbers only)
    #     """
    #     phone_data = self.check_num(phone_number)
    #     confirmation_code: Optional[str] = None  # Initialize the variable
    #
    #     if phone_data:
    #         confirmation_code = self.generate_confirmation_code()
    #         if phone_data[1] == "BY":
    #             params = {
    #                 "token": SenderServiceMixin.BY_TOKEN,
    #                 "message": f"Confirmation code: {confirmation_code}",
    #                 "phone_number": phone_data[0],
    #                 "alphaname_id": SenderServiceMixin.ALFA_SMS,
    #             }
    #
    #             self.send_code_to_phone(SenderServiceMixin.BELARUSIAN_SERVICE_ENDPOINT, params, "POST")
    #         elif phone_data[1] == "RU":
    #             params = {
    #                 "login": SenderServiceMixin.RUSSIAN_LOGIN,
    #                 "psw": SenderServiceMixin.RUSSIAN_PASS,
    #                 "phones": [phone_data[0]],
    #                 "mes": f"Confirmation code: {confirmation_code}",
    #                 "fmt": 3,
    #             }
    #
    #             self.send_code_to_phone(SenderServiceMixin.RUSSIAN_SERVICE_ENDPOINT, params, "GET")
    #
    #         self.save_confirmation_code(phone_number, confirmation_code)
    #
    #     return confirmation_code
    #
    # def send_code_to_phone(self, url: str, params: dict, method: str):
    #     """
    #     Send code to a phone number using the specified URL, parameters, and method
    #     """
    #     response = requests.request(
    #         method,
    #         url,
    #         params=params,
    #         headers
    #         ={"content-type": "application/json"},
    #     )
    #     print(response)

# def check_num(self, phone_number: str):
#     """
#     Приведение номера в нормальный вид
#     """
#     if not phone_number:
#         return None
#     by = re.compile(r"^(80|375)(25|29|33|44)\d{7}$")
#     ru = re.compile(r"^(7)(\d{3})\d{7}$")
#     if bool(by.match(phone_number)):
#         return phone_number, "BY"
#     elif bool(ru.match(phone_number)):
#         return phone_number, "RU"
#     return None
