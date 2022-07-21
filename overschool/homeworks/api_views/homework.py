from homeworks.models import Homework
from homeworks.serializers import HomeworkSerializer
from rest_framework import permissions, viewsets
from users.permissions import IsEditor


class HomeworkViewSet(viewsets.ModelViewSet):
    queryset = Homework.objects.all()
    serializer_class = HomeworkSerializer
    permission_classes = [permissions.IsAuthenticated, IsEditor | permissions.IsAdminUser]
