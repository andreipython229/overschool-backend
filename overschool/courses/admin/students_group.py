from courses.models import GroupCourseAccess, StudentsGroup, StudentsHistory
from django.contrib import admin


@admin.register(StudentsGroup)
class StudentsGroupAdmin(admin.ModelAdmin):
    pass


class GroupCourseAccessAdmin(admin.ModelAdmin):
    list_display = ("id", "current_group_name", "course_name", "group_name")
    list_display_links = ("id",)

    list_filter = ("current_group__name", "course__name", "group__name")
    search_fields = ["current_group__name", "course__name", "group__name"]

    def current_group_name(self, obj):
        return obj.current_group.name

    def group_name(self, obj):
        return obj.group.name

    def course_name(self, obj):
        return obj.course.name

    current_group_name.short_description = "Название группы"
    course_name.short_description = "Название курса"
    group_name.short_description = "Название группы на новом курсе"


admin.site.register(GroupCourseAccess, GroupCourseAccessAdmin)


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
