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
    'school', 'start_date', 'end_date', 'get_lessons_count', 'get_last_update_date', 'get_students_count',
    'get_completed_lessons_count')

    def get_lessons_count(self, obj):
        return obj.get_lessons_count()

    get_lessons_count.short_description = 'Total Lessons Count'

    def get_last_update_date(self, obj):
        return obj.get_last_update_date()

    get_last_update_date.short_description = 'Last Update Date'

    def get_students_count(self, obj):
        return obj.get_students_count()

    get_students_count.short_description = 'Total Students Count'

    def get_completed_lessons_count(self, obj):
        return obj.get_completed_lessons_count()

    get_completed_lessons_count.short_description = 'Completed Lessons Count'
