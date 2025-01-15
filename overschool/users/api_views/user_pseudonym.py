from common_services.mixins import LoggingMixin, WithHeadersViewSet
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin
from users.models import User

from ..models.user_pseudonym import UserPseudonym
from ..serializers.user_pseudonym import UserPseudonymSerializer


class UserPseudonymViewSet(
    LoggingMixin, WithHeadersViewSet, SchoolMixin, viewsets.ViewSet
):
    """
    API endpoint для работы с псевдонимами сотрудников школы
    """

    queryset = UserPseudonym.objects.all()
    serializer_class = UserPseudonymSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def retrieve(self, request, pk=None):
        """
        Возвращаем псевдоним сотрудника школы по его идентификатору
        """

        queryset = UserPseudonym.objects.all()
        user_pseudonym = get_object_or_404(queryset, pk=pk)
        serializer = UserPseudonymSerializer(user_pseudonym)
        return Response(serializer.data)

    def update(self, request, pk=None, school_name=None):
        """
        Обновление псевдонима сотрудника
        """

        user_id = request.data.get("user")
        try:
            user_instance = User.objects.get(pk=int(user_id))
        except User.DoesNotExist:
            raise Http404("Пользователь с таким идентификатором не найден")

        try:
            school_instance = School.objects.get(name=school_name)
        except School.DoesNotExist:
            raise Http404("Школа с таким именем не найдена")

        user_pseudonym = UserPseudonym.objects.filter(
            user=user_instance, school=school_instance
        ).first()
        if user_pseudonym:
            serializer = UserPseudonymSerializer(user_pseudonym, data=request.data)
        else:
            user_pseudonym = UserPseudonym.objects.create(
                user=user_instance, school=school_instance
            )
            serializer = UserPseudonymSerializer(user_pseudonym, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
