from rest_framework import decorators, mixins, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from users.models import Profile
from users.permissions import IsSuperAdmin
from users.serializers import ProfileSerializer


class ProfileViewSet(
    viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin
):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated | IsAdminUser]
