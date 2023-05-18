from datetime import datetime

from django.db.models import Avg, Count, F, Sum
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import StudentsGroup, UserProgressLogs, UserTest
from courses.paginators import UserHomeworkPagination
from courses.serializers import (GroupStudentsSerializer,
                                 GroupUsersByMonthSerializer,
                                 StudentsGroupSerializer)


class StudentsGroupViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = StudentsGroup.objects.all()
    serializer_class = StudentsGroupSerializer
    permission_classes = [permissions.DjangoModelPermissions]
    pagination_class = UserHomeworkPagination

    @action(detail=True)
    def stats(self, request, pk):
        """Статистика учеников группы"""
        group = self.get_object()
        queryset = StudentsGroup.objects.filter(group_id=group.pk)
        data = queryset.values(
            course=F("course_id"),
            email=F("students__email"),
            student_name=F("students__first_name"),
            student=F("students__id"),
            group=F("group_id"),
            last_active=F("students__date_joined"),
            update_date=F("students__date_joined"),
            ending_date=F("students__date_joined"),
        ).annotate(
            mark_sum=Sum("students__user_homeworks__mark"),
            average_mark=Avg("students__user_homeworks__mark"),
            progress=(F("students__user_progresses__lesson__order") * 100)
            / Count("course_id__sections__lessons__lesson_id"), # бьет ошибку
        )

        for row in data:
            mark_sum = (
                UserTest.objects.filter(user=row["student"])
                .values("user")
                .aggregate(mark_sum=Sum("success_percent"))["mark_sum"]
            )
            row["mark_sum"] += mark_sum // 10 if mark_sum is not None else 0 # бьет ошибку
        page = self.paginate_queryset(data)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(data)

    @action(detail=True)
    def user_count_by_month(self, request, pk):
        """Кол-во новых пользователей группы за месяц, по дефолту стоит текущий месяц,
        для конкретного месяца указываем параметр month_number="""

        group = self.get_object()
        queryset = StudentsGroup.objects.filter(
            group_id=group.pk,
            students__date_joined__month=request.GET["month_number"]
            if "month_number" in request.GET
            else datetime.now().month,
        )
        datas = queryset.values(group=F("group_id")).annotate(
            students_sum=Count("students__id")
        )
        for data in datas:
            data["graphic_data"] = queryset.values(
                group=F("group_id"), date=F("students__date_joined__day")
            ).annotate(students_sum=Count("students__id"))
        page = self.paginate_queryset(datas)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(datas)
