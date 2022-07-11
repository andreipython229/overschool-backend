from django.contrib import admin


class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_id', )