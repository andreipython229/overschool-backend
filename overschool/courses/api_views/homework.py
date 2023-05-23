from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Homework
from courses.serializers import HomeworkSerializer
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response


class HomeworkViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Homework.objects.all()
    serializer_class = HomeworkSerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра домашних заданий (любой пользователь)
            return permissions
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            # Разрешения для создания и изменения домашних заданий (только пользователи с группой 'Admin')
            user = self.request.user
            if user.groups.filter(name="Admin").exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            return permissions
