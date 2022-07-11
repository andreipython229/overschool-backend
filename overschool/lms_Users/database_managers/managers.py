from django.db import models


class SectionManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().order_by('order')


class LessonManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().order_by('order')

