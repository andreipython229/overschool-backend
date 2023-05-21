from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Question
from courses.serializers import QuestionSerializer
from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied


class QuestionViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра вопросов (любой пользователь)
            return permissions
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            # Разрешения для создания и изменения вопросов (только пользователи с группой 'Admin')
            user = self.request.user
            if user.groups.filter(name="Admin").exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            return permissions
