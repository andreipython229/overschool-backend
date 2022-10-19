from django.contrib import admin

from schools.models import School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    pass
