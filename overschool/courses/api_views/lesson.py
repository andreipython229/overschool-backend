from common_services.mixins import WithHeadersViewSet
from courses.models import Lesson
from courses.serializers import LessonSerializer
from rest_framework import permissions, viewsets


class LessonViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.DjangoModelPermissions]
