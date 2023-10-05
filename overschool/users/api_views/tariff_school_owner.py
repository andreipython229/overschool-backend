from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from schools.models import School
from schools.school_mixin import SchoolMixin

User = get_user_model()


class TariffOwner(serializers.Serializer):
    pass


class TariffSchoolOwner(LoggingMixin, WithHeadersViewSet, SchoolMixin, APIView):
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
        print(user)
        a = School.objects.get(name=school_name)
        print(a.owner)
        try:
            school = School.objects.get(name=school_name, owner=user)
        except School.DoesNotExist:
            return Response([])
        days_left = (school.purchased_tariff_end_date - timezone.now()).days
        data = {"tariff_name": school.tariff.name, "days_left": days_left}

        return Response(data)
