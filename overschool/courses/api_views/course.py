from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Course, Section, StudentsGroup
from courses.serializers import CourseSerializer, CourseStudentsSerializer
from django.db.models import Avg, Count, F, Sum
from homeworks.paginators import UserHomeworkPagination
from lesson_tests.models import UserTest
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from users.models import User
from datetime import datetime


## TODO: Надо переписать GET запрос на курсы, чтобы он возвращал вот такой json
## {"course_id": 0,
#   "course_name": "",
#    "sections": [
#    {"type" : "lesson/test/homework/vebinar??/section", "id": 0, "name": "", "order": 0},
#    ]
## TODO: Проверить все вьюхи, которые используют эти типы данных
## TODO: высчитывания баллов для конкретного юзера по курсу
class CourseViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.DjangoModelPermissions]

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
        course_copy = course.make_clone(attrs={"name": f"{course.name}-копия"})
        queryset = Course.objects.filter(pk=course_copy.pk)
        return Response(queryset.values())


class UsersCourse(LoggingMixin, WithHeadersViewSet, generics.ListAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.DjangoModelPermissions]
    pagination_class = UserHomeworkPagination

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset(course=request.GET['course_id'])
            paginator = self.pagination_class()
            data = paginator.paginate_queryset(request=request, queryset=queryset)
            return paginator.get_paginated_response(data=data)
        except KeyError as e:
            return Response(data={"status": "Error", "message": "No course_id"},
                            status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self, *args, **kwargs):
        queryset = StudentsGroup.objects.filter(course_id=kwargs['course'])
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
            progress=(Count("course_id__lessons__user_progresses__") * 100)
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


class CourseUsersByMonthView(LoggingMixin, WithHeadersViewSet, generics.ListAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.DjangoModelPermissions]

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset(
                month_number=request.GET['month_number'] if 'month_number' in request.GET else datetime.now().month,
                course_id=request.GET['course_id'])
            return Response(queryset, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response(data={"status": "Error", "message": "No course_id"}, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self, *args, **kwargs):
        queryset = StudentsGroup.objects.filter(course_id=kwargs['course_id'],
                                                students__date_joined__month=kwargs["month_number"])
        datas = queryset.values(course=F("course_id")).annotate(students_sum=Count("students__id"))
        for data in datas:
            data["graphic_data"] = queryset.values(course=F("course_id"),
                                                   date=F("students__date_joined__day")).annotate(
                students_sum=Count("students__id")
            )
        return datas
