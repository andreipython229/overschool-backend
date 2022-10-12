from django.conf import settings
from django.db import models


class AuthorMixin:
    """
    Миксин для дополнения полем author
    """

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Автор", help_text="Автор записи", on_delete=models.CASCADE, default=1
    )
