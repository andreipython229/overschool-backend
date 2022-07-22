from courses.models import Section
from django.contrib import admin


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    pass
