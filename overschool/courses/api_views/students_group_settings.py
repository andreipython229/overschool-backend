from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models.students.students_group_settings import StudentsGroupSettings
from courses.serializers import StudentsGroupSettingsSerializer
from rest_framework import permissions, viewsets
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied
from schools.models import School
from schools.school_mixin import SchoolMixin


class StudentsGroupSettingsViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet
):
    """Эндпоинт для получения и изменения настроек группы\n
    Эндпоинт для получения и изменения настроек группы"""

    serializer_class = StudentsGroupSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_school(self):
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        return school

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return (
                StudentsGroupSettings.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        return StudentsGroupSettings.objects.filter(
            students_group_settings_fk__course_id__school__school_id=self.get_school().school_id
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

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)
