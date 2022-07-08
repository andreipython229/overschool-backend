from django.db import models

from embed_video.fields import EmbedVideoField


class VideoModel(models.Model):
	tutorial_Title = models.CharField(max_length=200)
	tutorial_Body = models.TextField()
	tutorial_Video = EmbedVideoField()

	class Meta:
		verbose_name_plural = "Видосик"

	def __str__(self):
		return str(self.tutorial_Title) if self.tutorial_Title else " "
# Create your models here.

