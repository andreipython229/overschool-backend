from common_services.services import TruncateFileName, limit_image_size
from django.db import models
from schools.models import School


class SchoolDocuments(models.Model):
    user = models.ForeignKey(
        "users.User",  # Используем строку вместо get_user_model()
        on_delete=models.CASCADE
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE
    )
    stamp = models.FileField(
        help_text="Печать школы",
        verbose_name="Печать школы",
        max_length=300,
        validators=[limit_image_size],
        upload_to=TruncateFileName(300),
        blank=True,
        null=True,
    )
    signature = models.FileField(
        help_text="Подпись школы",
        verbose_name="Подпись школы",
        max_length=300,
        validators=[limit_image_size],
        upload_to=TruncateFileName(300),
        blank=True,
        null=True,
    )

    def str(self):
        return f"{self.user} - {self.school}"

    class Meta:
        verbose_name = "Документы школы"
        verbose_name_plural = "Документы школ"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["school"]),
        ]
        unique_together = (("user", "school"),)