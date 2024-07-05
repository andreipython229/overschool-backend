from django.db import models
from schools.models import School


class Referral(models.Model):
    referrer_school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="referrals",
        verbose_name="Школа-реферер",
        help_text="Школа-реферер",
    )
    referred_school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
        related_name="referred_by",
        verbose_name="Привлеченная школа",
        help_text="Привлеченная школа",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время создания реферала",
        help_text="Дата и время создания реферала",
    )

    class Meta:
        verbose_name = "Реферал"
        verbose_name_plural = "Рефералы"

    def __str__(self):
        return f"{self.referrer_school.name} привлекла {self.referred_school.name}"


class ReferralClick(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="referral_clicks",
        verbose_name="Школа",
        help_text="Школа, чей реферальный код был использован",
    )
    ip_address = models.GenericIPAddressField(
        verbose_name="IP-адрес", help_text="IP-адрес, с которого был совершен переход"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время перехода",
        help_text="Дата и время перехода",
    )
    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name="User Agent",
        help_text="Информация о браузере и системе пользователя",
    )

    class Meta:
        verbose_name = "Переход по реферальной ссылке"
        verbose_name_plural = "Переходы по реферальным ссылкам"

    def __str__(self):
        return f"Переход по коду {self.school.name} с IP {self.ip_address}"
