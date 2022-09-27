from django.db import models
from users.models import User


class AuthorPublishedModel(models.Model):
    """
    Базовая модель для дополнения остальных полями published и author_id
    """

    published = models.BooleanField(
        default=False,
        verbose_name="Опубликовано?",
        help_text="Опубликовать запись или нет",
    )
    author_id = models.ForeignKey(User, verbose_name="Автор", help_text="Автор записи", on_delete=models.CASCADE,
    default=1)

    class Meta:
        abstract = True
