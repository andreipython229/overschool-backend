from common_services.mixins import WithHeadersViewSet
from rest_framework import permissions, viewsets
from users.models import Profile
from users.serializers import UserProfileSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny


class ProfileViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = (AllowAny,)
