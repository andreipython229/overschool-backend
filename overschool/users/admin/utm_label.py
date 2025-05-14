from django.contrib import admin
from ..models.utm_label import UtmLabel


@admin.register(UtmLabel)
class UtmLabelAdmin(admin.ModelAdmin):
    list_display = ('user', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content')
