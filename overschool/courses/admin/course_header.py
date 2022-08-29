from courses.models import CourseHeader
from django.contrib import admin


@admin.register(CourseHeader)
class CourseHeaderAdmin(admin.ModelAdmin):
    pass