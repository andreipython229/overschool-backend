from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions

from common_services.mixins import WithHeadersViewSet
from users.models import Profile
from users.permissions import OwnerProfilePermissions
from users.serializers import UserProfileSerializer


class ProfileViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [DjangoModelPermissions | OwnerProfilePermissions]
