from __future__ import annotations

import logging
import threading

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class SenderServiceMixin:
    """Functionalities for sending registration messages to students and managers"""

    def send_code_by_email(self, email: str, message: str, subject: str):
        """
        Send code by email in a separate thread
        """
        html_message = message
        text_message = strip_tags(message)

        def send_mail_task():
            try:
                msg = EmailMultiAlternatives(
                    subject, text_message, settings.DEFAULT_FROM_EMAIL, [email]
                )
                msg.attach_alternative(html_message, "text/html")
                msg.send(fail_silently=False)
                logger.info(f"Email successfully sent to {email}")
            except Exception as e:
                logger.error(f"Failed to send email to {email}: {str(e)}")

        # Запускаем отправку в отдельном потоке
        thread = threading.Thread(target=send_mail_task)
        thread.daemon = True  # Поток завершится, когда завершится основная программа
        thread.start()

        return {"status": "processing"}
