from django.db import models


class CourseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by("order")
