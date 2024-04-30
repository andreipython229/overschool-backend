from django.db import models
from django.contrib.auth import get_user_model
# Create your models here.
User = get_user_model()


class TgUsers(models.Model):

    id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID пользователя",
        help_text="Уникальный идентификатор пользователя",
    )

    tg_user_id = models.CharField(
        verbose_name="Телеграм ID пользователя",
        max_length=10,
        editable=False,
    )

    first_name = models.CharField(
        verbose_name="Имя",
        max_length=150,
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Пользователь плтаформы",
    )

    def __str__(self):
        return f"Телеграм пользователь {self.first_name} "

    class Meta:
        verbose_name = "Телеграм пользователь"
        verbose_name_plural = "Телеграм пользователи"