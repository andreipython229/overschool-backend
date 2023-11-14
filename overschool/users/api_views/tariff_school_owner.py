from common_services.mixins import WithHeadersViewSet
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
from courses.models import Course

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
            return Response([])

        if school.tariff.name == TariffPlan.INTERN.value:
            data = {"tariff_name": school.tariff.name, "days_left": None, "students": 0, "staff": 0}
            return Response(data)

        if school.purchased_tariff_end_date:
            days_left = (school.purchased_tariff_end_date - timezone.now()).days
        elif school.trial_end_date:
            days_left = (school.trial_end_date - timezone.now()).days
        else:
            days_left = None

        users = User.objects.filter(groups__school=school)

        students = 0
        staff = 0

        for user in users:
            user_group = UserGroup.objects.filter(user=user, school=school).first()
            if user_group:
                role_name = user_group.group.name
                if role_name == "Student":
                    students += 1
                else:
                    staff += 1
        courses_for_school = Course.objects.filter(school=school)
        number_of_courses = courses_for_school.count()

        data = {
            "tariff_name": school.tariff.name,
            "days_left": days_left,
            "students": students,
            "staff": staff,
            "tariff": school.tariff.id,
            "number_of_courses": number_of_courses
        }

        return Response(data)
