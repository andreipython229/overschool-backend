from courses.models import StudentsGroup, StudentsHistory
from django.contrib import admin


@admin.register(StudentsGroup)
class StudentsGroupAdmin(admin.ModelAdmin):
    pass


@admin.register(StudentsHistory)
class StudentsHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "course",
        "students_group",
        "date_added",
        "date_removed",
        "is_deleted",
    ]
    list_filter = ["date_added", "date_removed", "is_deleted"]
    search_fields = ["user__username", "students_group__name"]
    date_hierarchy = "date_added"
    readonly_fields = ["date_added", "date_removed"]

    def course(self, obj):
        return obj.students_group.course_id

    course.short_description = "Курс"
