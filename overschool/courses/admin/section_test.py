from django.contrib import admin

from courses.models import SectionTest


@admin.register(SectionTest)
class SectionTestAdmin(admin.ModelAdmin):
    pass
