from common_services.mixins import WithHeadersViewSet
from rest_framework import permissions, viewsets
from users.models import Profile
from users.serializers import UserProfileSerializer


class ProfileViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = UserProfileSerializer
