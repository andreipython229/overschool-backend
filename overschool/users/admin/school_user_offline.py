from django.contrib import admin

from users.models import CourseOffline, SchoolUserOffline

admin.site.register(CourseOffline)


@admin.register(SchoolUserOffline)
class StudentAdmin(admin.ModelAdmin):
    filter_horizontal = ["course"]
