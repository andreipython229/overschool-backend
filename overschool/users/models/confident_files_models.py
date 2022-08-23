from django.db import models


class Documents(models.Model):
    doc_name = models.CharField(max_length=100)
    doc = models.FileField(
        upload_to="documents",
        verbose_name="“Документы“",
        help_text="Документы ......",
    )

    def __str__(self):
        return str(self.doc_name)