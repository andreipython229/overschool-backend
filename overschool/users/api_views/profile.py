from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.yandex_client import remove_from_yandex, upload_user_avatar
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from users.models import Profile
from users.permissions import OwnerProfilePermissions
from users.serializers import UserProfileGetSerializer, UserProfileSerializer


class ProfileViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """Эндпоинт просмотра и изменения Profiles\n
    озвращаем только объекты пользователя, сделавшего запрос"""

    queryset = Profile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated | OwnerProfilePermissions]
    http_method_names = ["get", "put", "patch", "head"]

    def get_queryset(self):
        # Возвращаем только объекты пользователя, сделавшего запрос
        return Profile.objects.filter(user=self.request.user.id)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return UserProfileGetSerializer
        else:
            return UserProfileSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = UserProfileSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.FILES.get("avatar"):
            if instance.avatar:
                remove_from_yandex(str(instance.avatar))
            serializer.validated_data["avatar"] = upload_user_avatar(
                request.FILES["avatar"], instance.user.id
            )
        else:
            serializer.validated_data["avatar"] = instance.avatar

        serializer.save()

        serializer = UserProfileGetSerializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)
