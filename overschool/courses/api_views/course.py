from courses.serializers import CourseSerializer, CourseStudentsSerializer
from rest_framework import generics, status, permissions, viewsets
from users.models import User
from django.db.models import F, Sum, Avg, Count
from homeworks.paginators import UserHomeworkPagination
from lesson_tests.models import UserTest
from courses.models import StudentsGroup
from common_services.mixins import WithHeadersViewSet, LoggingMixin
from courses.models import Course, Section
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny


class CourseViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (AllowAny,)

    @action(detail=True)
    def sections(self, request, pk):
        course = self.get_object()

        sections = Section.objects.filter(course_id=course.pk).order_by("order")

        all_data = {}

        sect = "sections"
        all_data["course_id"] = f"{course.pk}"
        for section in sections:
            if sect in all_data.keys():
                all_data[sect].append(
                    {
                        "name": section.name,
                        "section_id": section.section_id,
                        "lessons": section.lessons.values("name", "lesson_id"),
                    }
                )

            else:
                all_data[sect] = []
                all_data[sect].append(
                    {
                        "name": section.name,
                        "section_id": section.section_id,
                        "lessons": section.lessons.values("name", "lesson_id"),
                    }
                )

        return Response(all_data)

    @action(detail=True)
    def clone(self, request, pk):
        course = self.get_object()
        course_copy = course.make_clone(attrs={'name': f'{course.name}-копия'})
        queryset = Course.objects.filter(pk=course_copy.pk)
        return Response(queryset.values())


class UsersCourse(LoggingMixin, WithHeadersViewSet, generics.ListAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    pagination_class = UserHomeworkPagination
    serializer_class = CourseStudentsSerializer

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
            course_id=1
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
