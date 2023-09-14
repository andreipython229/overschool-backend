from common_services.mixins import LoggingMixin, WithHeadersViewSet
from rest_framework import viewsets, status
from rest_framework.response import Response
from schools.models import School
from users.models import User
from users.permissions import OwnerUserPermissions
from users.serializers import UserSerializer, AllUsersSerializer


class UserViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """Возвращаем только объекты пользователя, сделавшего запрос\n
    <h2>/api/user/</h2>\n
    Возвращаем только объекты пользователя, сделавшего запрос"""

    serializer_class = UserSerializer
    permission_classes = [OwnerUserPermissions]
    http_method_names = ["get", "head"]

    def get_queryset(self):
        # Возвращаем только объекты пользователя, сделавшего запрос
        return User.objects.filter(id=self.request.user.id)


class AllUsersViewSet(viewsets.GenericViewSet):
    """Возвращаем всех пользователей\n
        <h2>/api/user/</h2>\n
        Возвращаем всех пользователей"""

    queryset = User.objects.all()
    serializer_class = AllUsersSerializer

    def list(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        print(school_name)
        # Найти объект школы по имени
        try:
            school = School.objects.get(name=school_name)
        except School.DoesNotExist:
            return Response({'error': 'School not found'}, status=status.HTTP_404_NOT_FOUND)

        # Фильтровать пользователей по школе
        queryset = User.objects.filter(groups__school=school)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)