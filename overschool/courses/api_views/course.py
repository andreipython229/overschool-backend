from datetime import datetime

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Course, Lesson, Section, StudentsGroup
from courses.serializers import CourseSerializer, CourseStudentsSerializer
from django.db.models import Avg, Count, F, Sum
from django.forms.models import model_to_dict
from homeworks.models import Homework
from homeworks.paginators import UserHomeworkPagination
from lesson_tests.models import SectionTest, UserTest
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from users.models import User


## TODO: Проверить все вьюхи, которые используют эти типы данных
## TODO: высчитывания баллов для конкретного юзера по курсу


class CourseViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.DjangoModelPermissions]

    @action(detail=True)
    def clone(self, request, pk):
        course = self.get_object()
        course_copy = course.make_clone(attrs={"name": f"{course.name}-копия"})
        queryset = Course.objects.filter(pk=course_copy.pk)
        return Response(queryset.values())


class CourseDataSet(LoggingMixin, WithHeadersViewSet, generics.ListAPIView):
    queryset = Course.objects.all()
    permission_classes = [permissions.DjangoModelPermissions]

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset(course=request.GET["course_id"])
            return Response(queryset)
        except KeyError:
            return Response(
                data={"status": "Error", "message": "No course_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get_queryset(self, *args, **kwargs):
        queryset = Course.objects.filter(course_id=kwargs["course"])
        data = queryset.values(
            course=F("course_id"),
            course_name=F("name"),
            section_name=F("sections__name"),
            section=F("sections__section_id"),
        )
        result_data = dict(
            course_name=data[0]["course_name"],
            course_id=data[0]["course"],
            sections=[],
        )
        types = {0: "homework", 1: "lesson", 2: "test"}
        for index, value in enumerate(data):
            result_data["sections"].append(
                {
                    "section_name": value["section_name"],
                    "section": value["section"],
                    "lessons": [],
                }
            )
            a = Homework.objects.filter(section=value["section"])
            b = Lesson.objects.filter(section=value["section"])
            c = SectionTest.objects.filter(section=value["section"])
            for i in enumerate((a, b, c)):
                for obj in i[1]:
                    dict_obj = model_to_dict(obj)
                    result_data["sections"][index]["lessons"].append(
                        {
                            "type": types[i[0]],
                            "order": dict_obj["order"],
                            "name": dict_obj["name"],
                            "id": obj.pk,
                        }
                    )
            result_data["sections"][index]["lessons"].sort(key=lambda x: x["order"])
        return result_data


class UsersCourse(LoggingMixin, WithHeadersViewSet, generics.ListAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.DjangoModelPermissions]
    pagination_class = UserHomeworkPagination

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset(course=request.GET["course_id"])
            paginator = self.pagination_class()
            data = paginator.paginate_queryset(request=request, queryset=queryset)
            return paginator.get_paginated_response(data=data)
        except KeyError as e:
            return Response(
                data={"status": "Error", "message": "No course_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get_queryset(self, *args, **kwargs):
        queryset = StudentsGroup.objects.filter(course_id=kwargs["course"])
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
                month_number=request.GET["month_number"]
                if "month_number" in request.GET
                else datetime.now().month,
                course_id=request.GET["course_id"],
            )
            return Response(queryset, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response(
                data={"status": "Error", "message": "No course_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get_queryset(self, *args, **kwargs):
        queryset = StudentsGroup.objects.filter(
            course_id=kwargs["course_id"],
            students__date_joined__month=kwargs["month_number"],
        )
        datas = queryset.values(course=F("course_id")).annotate(
            students_sum=Count("students__id")
        )
        for data in datas:
            data["graphic_data"] = queryset.values(
                course=F("course_id"), date=F("students__date_joined__day")
            ).annotate(students_sum=Count("students__id"))
        return datas
