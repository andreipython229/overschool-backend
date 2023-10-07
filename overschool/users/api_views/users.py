from common_services.mixins import LoggingMixin, WithHeadersViewSet
from rest_framework import status, viewsets
from rest_framework.response import Response
from schools.models import School
from users.models import User
from users.permissions import OwnerUserPermissions
from users.serializers import AllUsersSerializer, UserSerializer


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

        # Найти объект школы по имени
        try:
            school = School.objects.get(name=school_name)
        except School.DoesNotExist:
            return Response(
                {"error": "School not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Проверить, является ли текущий пользователь администратором указанной школы
        user = request.user
        is_admin = user.groups.filter(group__name="Admin", school=school).exists()

        if is_admin:
            # Если пользователь - админ, вернуть только пользователей из этой школы
            queryset = User.objects.filter(groups__school=school)
            serializer = self.get_serializer(
                queryset, many=True, context={"school": school}
            )
            return Response(serializer.data)
        else:
            # В противном случае вернуть ошибку доступа
            return Response(
                {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
            )
