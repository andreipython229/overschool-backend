from courses.models import SchoolHeader
from django.contrib import admin


@admin.register(SchoolHeader)
class SchoolHeaderAdmin(admin.ModelAdmin):
    pass