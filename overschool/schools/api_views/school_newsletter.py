from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from ..models import NewsletterTemplate
from ..serializers import NewsletterTemplateSerializer
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from schools.school_mixin import SchoolMixin
from users.models.user import User
from schools.models import School


class NewsletterTemplateViewSet(LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet):
    """
    API endpoint для работы с шаблонами рассылки
    """
    queryset = NewsletterTemplate.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NewsletterTemplateSerializer

    def get_permissions(self, *args, **kwargs):
        user = self.request.user
        school_name = self.request.GET.get('school_name')

        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

        if user.id == 154 or school_name == "OVERONE":
            return super().get_permissions()

        raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def create(self, request, *args, **kwargs):
        """
        Создание нового шаблона для рассылки.
        """

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        """
        Обновление шаблона рассылки.
        """

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        """
        Получение списка всех шаблонов рассылки.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["DELETE"])
    def delete(self, request, school_name=None):
        """
        Удаление шаблона рассылки.
        """
        template_id = request.data.get('id')
        if not template_id:
            return Response({"error": "ID не предоставлен"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            instance = NewsletterTemplate.objects.get(id=template_id)
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except NewsletterTemplate.DoesNotExist:
            return Response({"error": "Шаблон не найден"}, status=status.HTTP_404_NOT_FOUND)
