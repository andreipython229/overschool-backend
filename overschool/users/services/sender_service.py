from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class SenderServiceMixin:
    """Functionalities for sending registration messages to students and managers"""

    def send_code_by_email(self, email: str, message: str, subject: str):
        """
        Send code by email
        """
        html_message = message
        text_message = strip_tags(message)  # удаляем HTML-теги

        # Указываем тип содержимого как HTML
        msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [email])
        msg.attach_alternative(html_message, "text/html")

        try:
            msg.send()
        except Exception as e:
            return {"error": str(e), "status_code": 500}
