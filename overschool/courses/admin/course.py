from courses.models import Course
from django.contrib import admin


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    pass
