from django.contrib import admin

from courses.models import SchoolHeader


@admin.register(SchoolHeader)
class SchoolHeaderAdmin(admin.ModelAdmin):
    pass
