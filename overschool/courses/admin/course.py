from courses.models import Course
from django.contrib import admin


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_id', 'name', 'format', 'duration_days', 'price',
                    'description', 'photo']
