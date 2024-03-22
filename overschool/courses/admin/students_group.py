from courses.models import StudentsGroup, StudentsHistory
from django.contrib import admin


@admin.register(StudentsGroup)
class StudentsGroupAdmin(admin.ModelAdmin):
    pass


@admin.register(StudentsHistory)
class StudentsHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "students_group",
        "date_added",
        "date_removed",
        "is_deleted",
    ]
    list_filter = ["date_added", "date_removed", "is_deleted"]
    search_fields = ["user__username", "students_group__name"]
    date_hierarchy = "date_added"
    readonly_fields = ["date_added", "date_removed"]
