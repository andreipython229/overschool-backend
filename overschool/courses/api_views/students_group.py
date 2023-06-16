from datetime import datetime

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import StudentsGroup, UserTest
from courses.paginators import UserHomeworkPagination
from courses.serializers import (
    GroupStudentsSerializer,
    GroupUsersByMonthSerializer,
    StudentsGroupSerializer,
)
from courses.models.students.students_group_settings import StudentsGroupSettings

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg, Count, F, Sum
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from schools.models import SchoolUser


class StudentsGroupViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    ''' Эндпоинт получения, создания, изменения групп студентов\n
        Разрешения для просмотра групп (любой пользователь)
        Разрешения для создания и изменения групп (только пользователи с группой 'Admin')
    '''
    queryset = StudentsGroup.objects.all()
    serializer_class = StudentsGroupSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = UserHomeworkPagination

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра групп (любой пользователь)
            return permissions
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            # Разрешения для создания и изменения групп (только пользователи с группой 'Admin')
            user = self.request.user
            if user.groups.filter(name="Admin").exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            return permissions

    def perform_create(self, serializer):
        # Создаём модель настроек группы
        group_settings_data = self.request.data.get('group_settings')
        if not group_settings_data:
            group_settings_data = {}
        group_settings = StudentsGroupSettings.objects.create(**group_settings_data)
        serializer.save(group_settings=group_settings)

        # Сохраняем группу студентов
        students_group = serializer.save()
        # Получаем всех студентов, которые были добавлены в группу
        students = self.request.data.get("students")
        for student_id in students:
            # Создаем запись в модели SchoolUser для каждого студента
            try:
                SchoolUser.objects.get(
                    user_id=student_id, school_id=students_group.course_id.school_id
                )
            except ObjectDoesNotExist:
                SchoolUser.objects.create(
                    user_id=student_id, school_id=students_group.course_id.school_id
                )

    @action(detail=True, methods=['GET'])
    def get_students_for_group(self, request, pk=None):
        """Все студенты одной группы"""

        group = self.get_object()
        students = group.students.all()

        student_data = []
        for student in students:
            student_data.append({
                'id': student.id,
                'username': student.username,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'email': student.email,
                # Добавьте другие поля пользователя, которые вам нужны
            })

        return Response(student_data)

    @action(detail=True)
    def stats(self, request, pk):
        """Статистика учеников группы\n
        Статистика учеников группы"""
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
                     / Count("course_id__sections__lessons__lesson_id"),  # бьет ошибку
        )

        for row in data:
            mark_sum = (
                UserTest.objects.filter(user=row["student"])
                    .values("user")
                    .aggregate(mark_sum=Sum("success_percent"))["mark_sum"]
            )
            row["mark_sum"] += (
                mark_sum // 10 if mark_sum is not None else 0
            )  # бьет ошибку
        page = self.paginate_queryset(data)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(data)

    @action(detail=True)
    def user_count_by_month(self, request, pk):
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