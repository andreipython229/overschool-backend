from __future__ import annotations

import os
import random
import re
import requests
from users.models import User
import redis
from django.conf import settings
from django.core.mail import send_mail
from users.tasks import send_code
from typing import Optional

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
        Save the confirmation code and other data in Redis
        """
        self.REDIS_INSTANCE.set(email, confirmation_code)

    def send_code_by_email(self, email: str, user: User) -> Optional[str]:
        """
        Send code by email
        """
        confirmation_code = self.generate_confirmation_code()
        self.save_confirmation_code(email, confirmation_code)

        subject = 'Confirmation Code'
        message = f'Your confirmation code: {confirmation_code}'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]

        send_mail(subject, message, from_email, recipient_list)

        return confirmation_code

    def send_code_by_phone(self, phone: str, user: User) -> Optional[str]:
        """
        Send code to a phone number (currently supports Belarusian and Russian numbers only)
        """
        phone_data = self.check_num(phone)
        confirmation_code: Optional[str] = None  # Initialize the variable

        if phone_data:
            confirmation_code = self.generate_confirmation_code()
            if phone_data[1] == "BY":
                params = {
                    "token": SenderServiceMixin.BY_TOKEN,
                    "message": f"Confirmation code: {confirmation_code}",
                    "phone": phone_data[0],
                    "alphaname_id": SenderServiceMixin.ALFA_SMS,
                }

                send_code.send_code_to_phone(SenderServiceMixin.BELARUSIAN_SERVICE_ENDPOINT, params, "post")
            elif phone_data[1] == "RU":
                params = {
                    "login": SenderServiceMixin.RUSSIAN_LOGIN,
                    "psw": SenderServiceMixin.RUSSIAN_PASS,
                    "phones": [phone_data[0]],
                    "mes": f"Confirmation code: {confirmation_code}",
                    "fmt": 3,
                }

                send_code.send_code_to_phone(SenderServiceMixin.RUSSIAN_SERVICE_ENDPOINT, params, "get")

            self.save_confirmation_code(phone, confirmation_code)

        return confirmation_code

    def send_code_for_password_reset_by_email(self, email):
        # Generate password reset code
        reset_code = self.generate_confirmation_code()

        # Send password reset code via email
        subject = 'Password Reset Code'
        message = f'Your password reset code is: {reset_code}'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]

        send_mail(subject, message, from_email, recipient_list)

        # Save password reset code in Redis or other storage
        self.save_reset_code(email, reset_code)

        return reset_code

    def send_code_for_password_reset_by_phone(self, phone, user_type):
        # Generate password reset code
        reset_code = self.generate_confirmation_code()

        # Send password reset code to phone
        params = {
            "token": SenderServiceMixin.BY_TOKEN,
            "message": f"Your password reset code: {reset_code}",
            "phone": phone,
            "alphaname_id": SenderServiceMixin.ALFA_SMS,
        }
        response = requests.post(SenderServiceMixin.BELARUSIAN_SERVICE_ENDPOINT, params)

        if response.status_code == 200:
            # Save password reset code in Redis or other storage
            self.save_reset_code(phone, reset_code)
            return reset_code
        else:
            # Error handling for SMS sending
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
