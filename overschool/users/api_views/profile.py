from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from users.models import Profile
from users.permissions import OwnerProfilePermissions
from users.serializers import UserProfileGetSerializer, UserProfileSerializer

s3 = UploadToS3()


class ProfileViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """Эндпоинт просмотра и изменения Profile\n
    <h2>/api/profile/</h2>\n
    возвращаем только объекты пользователя, сделавшего запрос"""

    queryset = Profile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated | OwnerProfilePermissions]
    http_method_names = ["get", "put", "patch", "head"]

    # parser_classes = (MultiPartParser,)

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
                s3.delete_file(str(instance.avatar))
            serializer.validated_data["avatar"] = s3.upload_avatar(
                request.FILES["avatar"], instance.user.id
            )
        else:
            serializer.validated_data["avatar"] = instance.avatar

        serializer.save()

        serializer = UserProfileGetSerializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)


ProfileViewSet = apply_swagger_auto_schema(tags=["profiles"])(ProfileViewSet)
