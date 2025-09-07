from django.db import models
from django.utils import timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from users.models.user import User
    from schools.models.school import School


class UserPseudonym(models.Model):
    """
    Модель псевдонима сотрудника в школе
    """

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="pseudonyms_as_user",
        verbose_name="Пользователь",
        help_text="Пользователь, которому принадлежит псевдоним",
    )
    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="pseudonyms_as_school",
        verbose_name="Школа",
        help_text="Школа, в которой используется псевдоним",
    )
    pseudonym = models.CharField(
        verbose_name="Псевдоним сотрудника",
        help_text="Псевдоним, используемый сотрудником в рамках школы",
        max_length=150,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.user} ({self.school}): {self.pseudonym or '—'}"

    class Meta:
        verbose_name = "Псевдоним сотрудника школы"
        verbose_name_plural = "Псевдонимы сотрудников школы"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["school"]),
            models.Index(fields=["pseudonym"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "school"],
                name="unique_user_school_pseudonym"
            )
        ]