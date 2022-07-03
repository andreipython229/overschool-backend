from django.contrib import admin
from embed_video.admin import AdminVideoMixin
from .models import VideoModel


class VideoModelAdmin(AdminVideoMixin, admin.ModelAdmin):
	list_display = ['tutorial_Title', 'tutorial_Body', 'tutorial_Video']


admin.site.register(VideoModel, VideoModelAdmin)
