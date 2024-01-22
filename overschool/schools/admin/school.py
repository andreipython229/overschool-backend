from django.contrib import admin
from schools.models import School, Tariff, SchoolStatistics


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    pass


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    pass


@admin.register(SchoolStatistics)
class SchoolStatisticsAdmin(admin.ModelAdmin):
    list_display = (
        'school', 'start_date', 'end_date', 'total_lessons_count', 'last_update_date', 'total_students_count',
        'completed_lessons_count'
    )
    list_filter = ('school__name', 'start_date', 'end_date')
    search_fields = ['school__name']
    list_select_related = ['school']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('school')

    def total_lessons_count(self, obj):
        return obj.get_lessons_count()

    total_lessons_count.short_description = 'Total Lessons Count'

    def last_update_date(self, obj):
        return obj.get_last_update_date()

    last_update_date.short_description = 'Last Update Date'

    def total_students_count(self, obj):
        return obj.get_students_count()

    total_students_count.short_description = 'Total Students Count'

    def completed_lessons_count(self, obj):
        return obj.get_completed_lessons_count()

    completed_lessons_count.short_description = 'Completed Lessons Count'
