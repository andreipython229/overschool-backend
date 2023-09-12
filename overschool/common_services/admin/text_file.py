from django.contrib import admin

from common_services.models import TextFile


@admin.register(TextFile)
class TextFileAdmin(admin.ModelAdmin):
    pass
