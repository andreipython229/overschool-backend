from django.contrib import admin

from common_services.models import AudioFile


@admin.register(AudioFile)
class AudioFileAdmin(admin.ModelAdmin):
    pass
