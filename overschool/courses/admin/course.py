from courses.models import Course, CourseAppeals
from django.contrib import admin


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        "course_id",
        "name",
        "is_catalog",
        "format",
        "duration_days",
        "price",
        "description",
        "photo",
    ]


@admin.register(CourseAppeals)
class CourseAppealsAdmin(admin.ModelAdmin):
    pass
