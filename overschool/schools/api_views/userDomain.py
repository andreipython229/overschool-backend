from common_services.mixins import LoggingMixin, WithHeadersViewSet
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from schools.models import Domain, School
from schools.school_mixin import SchoolMixin
from schools.serializers import DomainSerializer


class DomainViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet
):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        if user.groups.filter(group__name="Admin", school=school).exists():
            return super().get_permissions()
        else:
            if self.action in [
                "list",
                "retrieve",
            ]:
                user = self.request.user
                if user.is_anonymous:
                    raise PermissionDenied("У вас нет прав для выполнения этого действия.")
                else:
                    return super().get_permissions()
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")


    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return (
                Domain.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        return self.queryset.filter(school=school)

    def perform_create(self, serializer):
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        serializer.save(school=school)


class UnconfiguredDomainSerializer(serializers.Serializer):
    pass


class UnconfiguredDomainViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ViewSet):
    serializer_class = UnconfiguredDomainSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Получение списка неподключенных доменов",
        tags=["domains"],
    )
    def list(self, request):
        # Фильтруем домены и извлекаем уникальные имена
        unconfigured_domains = Domain.objects.filter(nginx_configured=False).distinct()
        domain_names = unconfigured_domains.values_list(
            "domain_name", flat=True
        ).distinct()

        # Возвращаем список уникальных имен доменов
        return Response(list(domain_names))

    @swagger_auto_schema(
        operation_summary="Обновление статуса конфигурации доменов",
        request_body=openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(type=openapi.TYPE_STRING),
            description="List of domain names to be updated",
        ),
        tags=["domains"],
    )
    @action(detail=False, methods=["post"])
    def update_domains(self, request):
        # Получаем список доменных имен из запроса
        domain_names = request.data

        if not domain_names or not isinstance(domain_names, list):
            return Response(
                {"error": "No domain names provided or invalid format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Обновляем поле nginx_configured для соответствующих доменов
        updated_count = Domain.objects.filter(domain_name__in=domain_names).update(
            nginx_configured=True
        )

        # Возвращаем количество обновленных доменов
        return Response({"updated_count": updated_count}, status=status.HTTP_200_OK)


class ConfiguredDomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ['id', 'school', 'domain_name']


class ConfiguredDomainViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ViewSet):
    serializer_class = ConfiguredDomainSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Получение списка подключенных доменов",
        tags=["domains"],
    )
    def list(self, request):
        configured_domains = Domain.objects.filter(nginx_configured=True).distinct()
        serializer = ConfiguredDomainSerializer(configured_domains, many=True)
        return Response(serializer.data)
