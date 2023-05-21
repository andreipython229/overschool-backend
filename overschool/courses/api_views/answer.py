from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Answer
from courses.serializers import AnswerSerializer
from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied


class AnswerViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра ответов к тестам (любой пользователь)
            return permissions
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            # Разрешения для создания и изменения ответов к тестам (только пользователи с группой 'Admin')
            user = self.request.user
            if user.groups.filter(name="Admin").exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            return permissions
