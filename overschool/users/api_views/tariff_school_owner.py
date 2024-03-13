from common_services.mixins import WithHeadersViewSet
from courses.models import Course
from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from schools.models import School, TariffPlan
from schools.school_mixin import SchoolMixin
from users.models import UserGroup
from datetime import datetime

User = get_user_model()


class TariffOwner(serializers.Serializer):
    pass


class TariffSchoolOwner(WithHeadersViewSet, SchoolMixin, APIView):
    """
    Эндпоинт тарифа школы владельца
    """

    permission_classes = [IsAuthenticated]
    serializer_class = TariffOwner

    @swagger_auto_schema(
        tags=["tariff owner"],
        operation_description="Получение тарифа школы владельца",
        operation_summary="Получение тарифа школы владельца",
    )
    def get(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        user = self.request.user

        try:
            school = School.objects.get(name=school_name, owner=user)
        except School.DoesNotExist:
            return Response({"error": "School not found"})

        if not school.tariff:
            return Response({"error": "No tariff found for this school"})

        # Вычисление оставшихся дней
        days_left = (
            (school.purchased_tariff_end_date - timezone.now()).days
            if school.purchased_tariff_end_date
            else (school.trial_end_date - timezone.now()).days
            if school.trial_end_date
            else None
        )

        # Подсчет количества студентов и сотрудников
        students = UserGroup.objects.filter(
            school=school, group__name="Student"
        ).count()
        staff = (
            UserGroup.objects.filter(school=school)
            .exclude(group__name="Student")
            .count()
        )

        # Получение количества курсов для школы
        number_of_courses = Course.objects.filter(school=school).count()

        # Количество добавленных студентов в месяц
        current_datetime = datetime.now()
        current_month = current_datetime.month
        current_year = current_datetime.year

        student_count_by_month = UserGroup.objects.filter(
            group__name="Student",
            school=school,
            created_at__year=current_year,
            created_at__month=current_month,
        ).count()

        # Подготовка данных о тарифе
        tariff_details = {
            "id": school.tariff.id,
            "name": school.tariff.name,
            "number_of_courses": school.tariff.number_of_courses,
            "number_of_staff": school.tariff.number_of_staff,
            "students_per_month": school.tariff.students_per_month,
            "total_students": school.tariff.total_students,
            "price": school.tariff.price,
            "student_count_by_month": student_count_by_month
        }

        data = {
            "tariff_name": school.tariff.name,
            "days_left": days_left,
            "students": students,
            "staff": staff,
            "tariff_details": tariff_details,
            "number_of_courses": number_of_courses,
        }

        return Response(data)
