from courses.models import StudentsGroup
from django.contrib import admin


@admin.register(StudentsGroup)
class StudentsGroupAdmin(admin.ModelAdmin):
    pass