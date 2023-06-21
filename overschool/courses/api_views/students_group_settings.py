from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models.students.students_group_settings import StudentsGroupSettings
from courses.serializers import StudentsGroupSettingsSerializer
from rest_framework import permissions, viewsets
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied


class StudentsGroupSettingsViewSet(
    LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet
):
    """Эндпоинт для получения и изменения настроек группы\n
    Эндпоинт для получения и изменения настроек группы"""

    queryset = StudentsGroupSettings.objects.all()
    serializer_class = StudentsGroupSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра групп (любой пользователь)
            return permissions
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            # Разрешения для создания и изменения групп (только пользователи с группой 'Admin')
            user = self.request.user
            if user.groups.filter(group__name="Admin").exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            return permissions

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)
