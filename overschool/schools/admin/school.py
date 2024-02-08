from datetime import datetime

from django.contrib import admin
from rangefilter.filters import DateRangeFilter, DateRangeFilterBuilder
from schools.models import School, SchoolStatistics, Tariff


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    pass


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    pass


@admin.register(SchoolStatistics)
class SchoolStatisticsAdmin(admin.ModelAdmin):
    list_display = (
        "school",
        "total_lessons_count",
        "last_update_date",
        "total_students_count",
        "completed_lessons_count",
    )
    list_filter = (
        (
            "school__course_school__group_course_fk__students__user_progresses__updated_at",
            DateRangeFilter,
        ),
        "school__name",
    )
    search_fields = ["school__name"]
    list_select_related = ["school"]

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.end_date = None
        self.start_date = None

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("school")
        self.start_date = request.GET.get(
            "school__course_school__group_course_fk__students__user_progresses__updated_at__range__gte"
        )
        self.end_date = request.GET.get(
            "school__course_school__group_course_fk__students__user_progresses__updated_at__range__lte"
        )
        return queryset

    def total_lessons_count(self, obj):
        return obj.get_lessons_count()

    total_lessons_count.short_description = "Total Lessons Count"

    def last_update_date(self, obj):
        return obj.get_last_update_date()

    last_update_date.short_description = "Last Update Date Lessons"

    def total_students_count(self, obj):
        return obj.get_students_count()

    total_students_count.short_description = "Total Students Count"

    def completed_lessons_count(self, obj):
        if not self.start_date and not self.end_date:
            return obj.get_completed_lessons_count()

        return obj.get_completed_lessons_count(
            start_date=datetime.strptime(self.start_date, "%d.%m.%Y").strftime(
                "%Y-%m-%d"
            )
            if self.start_date
            else None,
            end_date=datetime.strptime(self.end_date, "%d.%m.%Y").strftime("%Y-%m-%d")
            if self.end_date
            else None,
        )

    completed_lessons_count.short_description = "Completed Lessons Count"
