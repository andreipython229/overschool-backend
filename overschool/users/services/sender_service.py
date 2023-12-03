from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail


class SenderServiceMixin:
    """Functionalities for sending registration messages to students and managers"""

    def send_code_by_email(self, email: str, message: str, subject: str):
        """
        Send code by email
        """
        # Send the confirmation code via email
        subject = subject
        message = message
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]

        try:
            send_mail(
                subject,
                message,
                from_email,
                recipient_list,
            )
        except Exception as e:
            return {"error": str(e), "status_code": 500}
