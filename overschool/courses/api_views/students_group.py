from datetime import datetime

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Course, StudentsGroup, UserTest
from courses.models.students.students_group_settings import StudentsGroupSettings
from courses.paginators import UserHomeworkPagination
from courses.serializers import (
    GroupStudentsSerializer,
    GroupUsersByMonthSerializer,
    SectionSerializer,
    StudentsGroupSerializer,
)
from django.contrib.auth.models import Group
from django.db.models import Avg, Count, F, Sum
from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin
from users.models import UserGroup


class StudentsGroupViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet
):
    """Эндпоинт получения, создания, изменения групп студентов\n
    Разрешения для просмотра групп (любой пользователь)
    Разрешения для создания и изменения групп (только пользователи с группой 'Admin')
    """

    serializer_class = StudentsGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = UserHomeworkPagination

    def get_school(self):
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        return school

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return (
                StudentsGroup.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        return StudentsGroup.objects.filter(
            course_id__school__school_id=self.get_school().school_id
        )

    def get_permissions(self):
        permissions = super().get_permissions()
        user = self.request.user
        school = self.get_school()
        # Разрешения только для пользователей данной школы
        if user.groups.filter(school=school).exists():
            if self.action in ["list", "retrieve"]:
                # Разрешения для просмотра групп (любой пользователь школы)
                return permissions
            elif self.action in ["create", "update", "partial_update", "destroy"]:
                # Разрешения для создания и изменения групп (только пользователи с группой 'Admin')
                if user.groups.filter(school=school, group__name="Admin").exists():
                    return permissions
                else:
                    raise PermissionDenied(
                        "У вас нет прав для выполнения этого действия."
                    )
            else:
                return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def perform_create(self, serializer):
        serializer.is_valid()
        course = serializer.validated_data["course_id"]
        school = self.get_school()
        teacher = serializer.validated_data["teacher_id"]

        if course.school != school:
            raise serializers.ValidationError("Курс не относится к вашей школе.")
        if not teacher.groups.filter(school=school, group__name="Teacher").exists():
            raise serializers.ValidationError(
                "Пользователь, указанный в поле 'teacher_id', не является учителем в вашей школе."
            )

        # Создаём модель настроек группы
        group_settings_data = self.request.data.get("group_settings")
        if not group_settings_data:
            group_settings_data = {}
        group_settings = StudentsGroupSettings.objects.create(**group_settings_data)
        serializer.save(group_settings=group_settings)

        # Сохраняем группу студентов
        serializer.save()
        # Получаем всех студентов, которые были добавлены в группу
        students = serializer.validated_data.get("students")
        group = Group.objects.get(name="Student")
        for student in students:
            # Создаем роли студентов для конкретной школы
            if not UserGroup.objects.filter(
                user=student, group=group, school=school
            ).exists():
                UserGroup.objects.create(user=student, group=group, school=school)

    def perform_update(self, serializer):
        course = serializer.validated_data["course_id"]
        school = self.get_school()
        teacher = serializer.validated_data["teacher_id"]

        if course.school != school:
            raise serializers.ValidationError("Курс не относится к вашей школе.")
        if not teacher.groups.filter(school=school, group__name="Teacher").exists():
            raise serializers.ValidationError(
                "Пользователь, указанный в поле 'teacher_id', не является учителем в вашей школе."
            )

        students = serializer.validated_data.get("students")
        group = Group.objects.get(name="Student")
        for student in students:
            # Создаем роли вновь добавленных студентов для конкретной школы
            if not student.students_group_fk.filter(pk=self.get_object().pk).exists():
                if not UserGroup.objects.filter(
                    user=student, group=group, school=school
                ).exists():
                    UserGroup.objects.create(user=student, group=group, school=school)

        serializer.save()

    @action(detail=True, methods=["GET"])
    def get_students_for_group(self, request, pk=None, *args, **kwargs):
        """Все студенты одной группы"""
        course = self.get_object()
        group = self.get_object()
        students = group.students.all()

        student_data = []
        for student in students:

            student_data.append(
                {
                    "group_id": group.group_id,
                    "group_name": group.name,
                    "id": student.id,
                    "username": student.username,
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "email": student.email,
                    "course_name": course.name,
                    "last_active": student.date_joined,
                    "update_date": student.date_joined,
                    "ending_date": student.date_joined,
                    "mark_sum": student.user_homeworks.aggregate(mark_sum=Sum("mark"))[
                        "mark_sum"
                    ],
                    "average_mark": student.user_homeworks.aggregate(
                        average_mark=Avg("mark")
                    )["average_mark"],
                    "section": SectionSerializer(
                        course.course_id.sections.all(), many=True
                    ).data,
                }
            )
        return Response(student_data)

    @action(detail=True)
    def user_count_by_month(self, request, pk, *args, **kwargs):
        """Кол-во новых пользователей группы за месяц\n
        по дефолту стоит текущий месяц,
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
