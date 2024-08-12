from datetime import datetime

from django.contrib import admin
from django.db.models import Count
from rangefilter.filters import DateRangeFilter, DateRangeFilterBuilder
from schools.models import School, SchoolStatistics, SchoolTask, Tariff


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner_email",
        "owner_phone",
        "tariff",
        "purchased_tariff_end_date",
        "trial_end_date",
    )
    list_filter = (
        "name",
        "owner__email",
        "owner__phone_number",
        "tariff",
    )
    search_fields = (
        "name",
        "owner__email",
        "owner__phone_number",
    )
    ordering = ("purchased_tariff_end_date", "trial_end_date")

    def owner_email(self, obj):
        return obj.owner.email

    owner_email.short_description = "Email владельца"

    def owner_phone(self, obj):
        return obj.owner.phone_number

    owner_phone.short_description = "Телефон владельца"


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    pass


@admin.register(SchoolTask)
class TaskAdmin(admin.ModelAdmin):
    pass


class CustomSortFilter(admin.SimpleListFilter):
    title = "Сортировка"

    parameter_name = "sort"

    def lookups(self, request, model_admin):
        return (
            ("asc_less", "Уроки по возрастанию"),
            ("desc_less", "Уроки по убыванию"),
            ("asc_stud", "Студенты по возрастанию"),
            ("desc_stud", "Студенты по убыванию"),
            ("asc_comply", "Прогресс по возрастанию"),
            ("desc_comply", "Прогресс по убыванию"),
        )

    def queryset(self, request, queryset):
        order = self.value()

        if order == "asc_less":
            queryset = queryset.annotate(
                lessons_count=Count("school__course_school__sections__lessons")
            )
            queryset = queryset.order_by("lessons_count")
        elif order == "desc_less":
            queryset = queryset.annotate(
                lessons_count=Count("school__course_school__sections__lessons")
            )
            queryset = queryset.order_by("-lessons_count")
        elif order == "asc_stud":
            queryset = queryset.annotate(students_count=Count("school__groups"))
            queryset = queryset.order_by("students_count")
        elif order == "desc_stud":
            queryset = queryset.annotate(students_count=Count("school__groups"))
            queryset = queryset.order_by("-students_count")
        elif order == "asc_comply":
            queryset = queryset.annotate(
                progress_count=Count(
                    "school__course_school__sections__lessons__user_progresses"
                )
            )
            queryset = queryset.order_by("progress_count")
        elif order == "desc_comply":
            queryset = queryset.annotate(
                progress_count=Count(
                    "school__course_school__sections__lessons__user_progresses"
                )
            )
            queryset = queryset.order_by("-progress_count")
        return queryset


class CustomDateRangeFilter(DateRangeFilter):
    def queryset(self, request, queryset):
        return queryset


@admin.register(SchoolStatistics)
class SchoolStatisticsAdmin(admin.ModelAdmin):
    list_display = (
        "school",
        "school_owner_phone",
        "school_owner_email",
        "school_created_at",
        "total_lessons_count",
        "last_update_date",
        "added_students_count",
        "completed_lessons_count",
    )
    list_filter = (
        CustomSortFilter,
        (
            "school__updated_at",
            CustomDateRangeFilter,
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
        self.start_date = request.GET.get("school__updated_at__range__gte")
        self.end_date = request.GET.get("school__updated_at__range__lte")
        return queryset.order_by("-school__created_at")

    def school_owner_phone(self, obj):
        return obj.school.owner.phone_number

    school_owner_phone.short_description = "Телефон владельца школы"

    def school_owner_email(self, obj):
        return obj.school.owner.email

    school_owner_email.short_description = "Email владельца школы"

    def school_created_at(self, obj):
        return obj.school.created_at

    school_created_at.short_description = "Дата создания школы"

    def total_lessons_count(self, obj):
        return obj.get_lessons_count()

    total_lessons_count.short_description = "Количество занятий курса"

    def last_update_date(self, obj):
        return obj.get_last_update_date()

    last_update_date.short_description = "Последнее обновление курса"

    def added_students_count(self, obj):
        if not self.start_date and not self.end_date:
            return obj.get_added_students_count()

        return obj.get_added_students_count(
            start_date=datetime.strptime(self.start_date, "%d.%m.%Y").strftime(
                "%Y-%m-%d"
            )
            if self.start_date
            else None,
            end_date=datetime.strptime(self.end_date, "%d.%m.%Y").strftime("%Y-%m-%d")
            if self.end_date
            else None,
        )

    added_students_count.short_description = "Количество добавленных студентов"

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

    completed_lessons_count.short_description = (
        "Количество пройденных занятий студентами"
    )
