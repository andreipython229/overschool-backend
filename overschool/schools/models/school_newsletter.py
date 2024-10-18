from django.db import models
from users.models.user import User

from . import School


class NewsletterTemplate(models.Model):
    template_name = models.CharField(max_length=255, verbose_name="Имя шаблона")
    text = models.TextField(verbose_name="Текст шаблона")
    delay_days = models.PositiveIntegerField(
        verbose_name="Количество дней после регистрации для рассылки"
    )
    is_public = models.BooleanField(default=False, verbose_name="Рассылать ли шаблон")
    template_created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата и время создания шаблона"
    )

    def __str__(self):
        return f"{self.template_name} (рассылка через: {self.delay_days} дней)"

    class Meta:
        verbose_name = "Шаблон для рассылки"
        verbose_name_plural = "Шаблоны для рассылки"
        indexes = [models.Index(fields=["template_name"])]


class SentNewsletter(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="sent_newsletters",
        verbose_name="Школа",
    )
    template = models.ForeignKey(
        NewsletterTemplate,
        on_delete=models.CASCADE,
        related_name="sent_newsletters",
        verbose_name="Шаблон рассылки",
    )
    sent_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата и время отправки"
    )

    def __str__(self):
        return f"Школа: {self.school.name}, Шаблон: {self.template.template_name}, Отправлено: {self.sent_at}"

    class Meta:
        verbose_name = "Отправленный шаблон"
        verbose_name_plural = "Отправленные шаблоны"
        indexes = [
            models.Index(fields=["school"]),
            models.Index(fields=["template"]),
        ]
