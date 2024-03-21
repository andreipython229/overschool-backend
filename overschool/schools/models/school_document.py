from common_services.services import TruncateFileName, limit_image_size
from django.contrib.auth import get_user_model
from django.db import models
from schools.models import School

User = get_user_model()


class SchoolDocuments(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
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

    def __str__(self):
        return f"{self.user} - {self.school}"

    class Meta:
        verbose_name = "Документы школы"
        verbose_name_plural = "Документы школ"
        unique_together = (("user", "school"),)
