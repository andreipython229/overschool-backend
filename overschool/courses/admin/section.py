from django.contrib import admin

from courses.models import Section


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ["section_id", "course", "name", "order"]
