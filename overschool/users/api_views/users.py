from common_services.mixins import LoggingMixin, WithHeadersViewSet
from rest_framework import permissions, viewsets
from users.models import User
from users.permissions import OwnerUserPermissions
from users.serializers import UserSerializer


class UserViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.DjangoModelPermissions | OwnerUserPermissions]
    http_method_names = ["get", "patch", "put", "head"]
