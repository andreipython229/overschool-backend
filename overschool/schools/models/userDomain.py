from django.db import models
from schools.models import School


class Domain(models.Model):
    school = models.OneToOneField(
        School, on_delete=models.CASCADE, related_name="domain", unique=True
    )
    domain_name = models.CharField(max_length=255, unique=True)
    nginx_configured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.domain_name

    class Meta:
        verbose_name = "Домен"
        verbose_name_plural = "Домены"
        indexes = [
            models.Index(fields=["domain_name"]),
            models.Index(fields=["nginx_configured"]),
            models.Index(fields=["school"]),
        ]
