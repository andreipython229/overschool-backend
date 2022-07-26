from courses.models import Lesson
from courses.serializers import LessonSerializer
from rest_framework import permissions, viewsets
from users.permissions import IsEditor


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated, IsEditor | permissions.IsAdminUser]
