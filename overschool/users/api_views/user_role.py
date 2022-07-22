from rest_framework import viewsets
from users.models import UserRole
from users.serializers import UserRoleSerializer


class UserRoleViewSet(viewsets.ModelViewSet):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
