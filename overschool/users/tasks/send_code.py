import requests
from django.conf import settings
from django.core.mail import EmailMessage

from overschool.celery import app
from users.services import *


@app.task
def send_code_to_phone(url: str, params: dict, method: str):
    requests.request(
        method,
        url,
        params=params,
        headers={"content-type": "application/json"},
    )


@app.task
def send_email(recipient_mail: str, message: str):
    EmailMessage(message, settings.DEFAULT_FROM_EMAIL, (recipient_mail,)).send(
        fail_silently=True
    )
