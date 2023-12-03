from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from django.http import HttpResponse
from rest_framework import status, viewsets
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
    permission_classes = [OwnerProfilePermissions]
    http_method_names = ["get", "put", "patch", "head"]

    def get_queryset(self):
        # Возвращаем только объекты пользователя, сделавшего запрос
        return Profile.objects.filter(user=self.request.user.id)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return UserProfileGetSerializer
        else:
            return UserProfileSerializer

    def list(self, request, *args, **kwargs):
        if self.request.user.is_anonymous:
            return HttpResponse(status=401)
        queryset = self.get_queryset()
        serializer = UserProfileGetSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = self.request.user
        user.email = (None,)
        user.save()
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
