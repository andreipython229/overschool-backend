from courses.models import Course, CourseAppeals
from django.contrib import admin
from rangefilter.filters import DateRangeFilter

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
    list_display = ('get_school_name', 'course','name', 'email', 'phone',  'created_at')
    list_filter = (('created_at', DateRangeFilter),'course__school__name', 'email', 'phone', 'name', 'course')
    search_fields = ('name', 'email', 'phone', 'course__name', 'course__school__name')
    ordering = ('-created_at',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('course__school')

    def get_school_name(self, obj):
        return obj.course.school.name

    get_school_name.short_description = 'Школа'
