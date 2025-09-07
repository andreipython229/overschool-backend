from django.db import models


class UserSubscription(models.Model):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Пользователь",
        help_text="Пользователь, у которого есть подписка",
    )
    subscription_id = models.CharField(
        max_length=255,
        verbose_name="ID подписки",
        help_text="Идентификатор подписки",
    )
    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Школа",
        help_text="Школа, к которой относится подписка",
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата окончания",
        help_text="Дата окончания подписки",
    )

    def __str__(self):
        return f"{self.user} - {self.subscription_id} - {self.school} - {self.expires_at}"

    class Meta:
        verbose_name = "Подписка пользователя"
        verbose_name_plural = "Подписки пользователей"
        unique_together = ("user", "school")
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["school"]),
            models.Index(fields=["expires_at"]),
        ]