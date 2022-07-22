from lesson_tests.models import LessonTest
from lesson_tests.serializers import TestSerializer
from rest_framework import permissions, viewsets
from users.permissions import IsEditor


class TestViewSet(viewsets.ModelViewSet):
    queryset = LessonTest.objects.all()
    serializer_class = TestSerializer
    permission_classes = [permissions.IsAuthenticated, IsEditor | permissions.IsAdminUser]
