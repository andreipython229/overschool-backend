from homeworks.models import UserHomework
from homeworks.serializers import UserHomeworkSerializer
from rest_framework import permissions, viewsets
from users.permissions import IsEditor


class UserHomeworkViewSet(viewsets.ModelViewSet):
    queryset = UserHomework.objects.all()
    serializer_class = UserHomeworkSerializer
    permission_classes = [permissions.IsAuthenticated, IsEditor | permissions.IsAdminUser]
