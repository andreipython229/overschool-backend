import requests
from django.conf import settings
from django.core.mail import EmailMessage
from django.core import mail
from overschool.celery import app
from users.services import *
from django.template.loader import render_to_string, get_template


@app.task
def send_code_to_phone(url: str, params: dict, method: str):
    response = requests.request(
        method,
        url,
        params=params,
        headers={"content-type": "application/json"},
    )
    print(response)


@app.task
def send_email(recipient_mail: str, message: str):
    message = get_template('email_notification_template.html').render({"register_url": message})
    msg = EmailMessage('Registration overschool', message, settings.DEFAULT_FROM_EMAIL, (recipient_mail,))
    msg.content_subtype = "html"
    msg.send(
        fail_silently=True
    )
