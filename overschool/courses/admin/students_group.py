from django.contrib import admin

from courses.models import StudentsGroup


@admin.register(StudentsGroup)
class StudentsGroupAdmin(admin.ModelAdmin):
    pass
