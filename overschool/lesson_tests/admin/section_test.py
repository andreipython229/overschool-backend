from django.contrib import admin

from lesson_tests.models import SectionTest


@admin.register(SectionTest)
class SectionTestAdmin(admin.ModelAdmin):
    pass
