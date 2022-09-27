from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import StudentsGroup
from courses.serializers import (
    GroupStudentsSerializer,
    GroupUsersByMonthSerializer,
    StudentsGroupSerializer,
)
from django.db.models import Avg, Count, F, Sum
from homeworks.paginators import UserHomeworkPagination
from lesson_tests.models import UserTest
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from users.models import User
from datetime import datetime


class StudentsGroupViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = StudentsGroup.objects.all()
    serializer_class = StudentsGroupSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class UsersGroup(LoggingMixin, WithHeadersViewSet, generics.ListAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.DjangoModelPermissions]
    pagination_class = UserHomeworkPagination

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset(group_id=request.GET['group_id'])
            paginator = self.pagination_class()
            data = paginator.paginate_queryset(request=request, queryset=queryset)
            return paginator.get_paginated_response(data=data)
        except KeyError as e:
            return Response(data={"status": "Error", "message": "No group_id"}, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self, *args, **kwargs):
        queryset = StudentsGroup.objects.filter(group_id=kwargs['group_id'])
        data = queryset.values(course=F("course_id"),
                               email=F("students__email"),
                               student_name=F("students__first_name"),
                               student=F("students__id"),
                               group=F("group_id"),
                               last_active=F("students__date_joined"),
                               update_date=F("students__date_joined"),
                               ending_date=F("students__date_joined")
                               ).annotate(
            mark_sum=Sum("students__user_homeworks__mark"),
            average_mark=Avg("students__user_homeworks__mark"),
            progress=(F("students__user_progresses__lesson__order") * 100)
                     / Count("course_id__sections__lessons__lesson_id"),
        )
        for row in data:
            mark_sum = (
                UserTest.objects.filter(user=row["student"])
                .values("user")
                .aggregate(mark_sum=Sum("success_percent"))["mark_sum"]
            )
            row["mark_sum"] += mark_sum // 10 if bool(mark_sum) else 0
        return data


class GroupUsersByMonthView(LoggingMixin, WithHeadersViewSet, generics.ListAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.DjangoModelPermissions]

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset(
                month_number=request.GET['month_number'] if 'month_number' in request.GET else datetime.now().month,
                group_id=request.GET['group_id'])
            return Response(queryset, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response(data={"status": "Error", "message": "No group_id"}, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self, *args, **kwargs):
        queryset = StudentsGroup.objects.filter(group_id=kwargs['group_id'],
                                                students__date_joined__month=kwargs["month_number"])
        datas = queryset.values(group=F("group_id")).annotate(students_sum=Count("students__id"))
        for data in datas:
            data["graphic_data"] = queryset.values(group=F("group_id"), date=F("students__date_joined__day")).annotate(
                students_sum=Count("students__id")
            )
        return datas
