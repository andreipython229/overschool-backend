from common_services.mixins import WithHeadersViewSet
from rest_framework import permissions, viewsets
from users.models import Profile
from users.permissions import OwnerProfilePermissions
from users.serializers import UserProfileSerializer


class ProfileViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated | OwnerProfilePermissions]


def get_queryset(self):
    if self.request.user.is_authenticated:
        user = self.request.user
        return Profile.objects.filter(user=user)
    else:
        return Profile.objects.none()