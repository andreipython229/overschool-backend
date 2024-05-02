from courses.models import GroupCourseAccess, StudentsGroup, StudentsHistory
from django.contrib import admin


@admin.register(StudentsGroup)
class StudentsGroupAdmin(admin.ModelAdmin):
    pass


class GroupCourseAccessAdmin(admin.ModelAdmin):
    list_display = ("id", "group_name", "course_name")
    list_display_links = ("id",)

    list_filter = ("group__name", "course__name")
    search_fields = ["group__name", "course__name"]

    def group_name(self, obj):
        return obj.group.name

    def course_name(self, obj):
        return obj.course.name

    group_name.short_description = "Название группы"
    course_name.short_description = "Название курса"


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
