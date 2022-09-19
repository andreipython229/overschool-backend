from common_services.mixins import WithHeadersViewSet, LoggingMixin
from courses.models import StudentsGroup
from courses.serializers import StudentsGroupSerializer, GroupStudentsSerializer, GroupUsersByMonthSerializer
from rest_framework import permissions, viewsets, generics, status
from homeworks.paginators import UserHomeworkPagination
from rest_framework.response import Response
from users.models import User
from django.db.models import F, Sum, Avg, Count
from lesson_tests.models import UserTest
from datetime import datetime


class StudentsGroupViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = StudentsGroup.objects.all()
    serializer_class = StudentsGroupSerializer
    permission_classes = [permissions.AllowAny]


class UsersGroup(LoggingMixin, WithHeadersViewSet, generics.ListAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    pagination_class = UserHomeworkPagination
    serializer_class = GroupStudentsSerializer

    def list(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            queryset = self.get_queryset(**serializer.data)
            paginator = self.pagination_class()
            data = paginator.paginate_queryset(request=request, queryset=queryset)
            return paginator.get_paginated_response(data=data)
        else:
            return Response(data=serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self, *args, **kwargs):
        queryset = StudentsGroup.objects.filter(
            group_id=1
        )
        data = queryset.values(email=F("students__email"),
                               student_name=F("students__first_name"),
                               student=F("students__user_id"),
                               group=F("group_id")).annotate(
            mark_sum=Sum("students__user_homeworks__mark"),
            average_mark=Avg("students__user_homeworks__mark"),
            progress=(F("students__user_progresses__lesson__order") * 100) / Count(
                "course_id__sections__lessons__lesson_id")
        )
        for row in data:
            mark_sum = \
                UserTest.objects.filter(user=row['student']).values('user').aggregate(mark_sum=Sum("success_percent"))[
                    'mark_sum']
            row['mark_sum'] += mark_sum // 10 if mark_sum else 0
        return data


class GroupUsersByMonthView(LoggingMixin, WithHeadersViewSet, generics.ListAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = GroupUsersByMonthSerializer

    def list(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            queryset = self.get_queryset(**serializer.data)
            return Response(queryset, status=status.HTTP_200_OK)
        else:
            return Response(data=serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self, *args, **kwargs):
        queryset = StudentsGroup.objects.filter(
            group_id=1,
            students__created_at__month=kwargs['month_number']
        )
        datas = queryset.values(group=F("group_id")).annotate(
            students_sum=Count("students__user_id")
        )
        for data in datas:
            data["graphic_data"] = queryset.values(group=F("group_id"), date=F("students__created_at__day")).annotate(
            students_sum=Count("students__user_id")
        )
        return datas
