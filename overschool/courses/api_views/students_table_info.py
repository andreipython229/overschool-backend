from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import StudentsTableInfo
from courses.serializers import (
    StudentsTableInfoDetailSerializer,
    StudentsTableInfoSerializer,
)
from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin


class StudentsTableInfoViewSet(WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet):
    """Эндпоинт табличной информации о студентах\n
    <h2>/api/{school_name}/students_table_info/</h2>\n
    Табличная информация о студентах
    """

    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "put", "patch", "head"]

    # parser_classes = (MultiPartParser,)

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(
            group__name__in=["Admin", "Teacher"], school=school_id
        ).exists():
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_serializer_class(self):
        if self.action == "update":
            return StudentsTableInfoDetailSerializer
        return StudentsTableInfoSerializer

    def get_queryset(self, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return (
                StudentsTableInfo.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        user = self.request.user
        return StudentsTableInfo.objects.filter(author=user, school=school_id)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


StudentsTableInfoViewSet = apply_swagger_auto_schema(
    tags=[
        "students_table_info",
    ]
)(StudentsTableInfoViewSet)
