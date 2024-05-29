from django.db import models

from schools.models import School


class Domain(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    domain_name = models.CharField(max_length=255)
    nginx_configured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.domain_name
