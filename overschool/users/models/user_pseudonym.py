from django.db import models
from django.utils import timezone

from .user import User
from schools.models.school import School


class UserPseudonym(models.Model):
    """Модель псевдонима сотрудника в школе"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pseudonyms_as_user'
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='pseudonyms_as_school'
    )
    pseudonym = models.CharField(
        verbose_name="Псевдоним сотрудника",
        max_length=150,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.user} ({self.school}): {self.pseudonym}"

    class Meta:
        verbose_name = "Псевдоним сотрудника школы"
        verbose_name_plural = "Псевдоним сотрудника школы"
