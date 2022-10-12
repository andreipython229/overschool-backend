from courses.models import SectionTest
from django.contrib import admin


@admin.register(SectionTest)
class SectionTestAdmin(admin.ModelAdmin):
    pass
