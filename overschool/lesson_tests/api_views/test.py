from common_services.mixins import WithHeadersViewSet
from lesson_tests.models import LessonTest
from lesson_tests.serializers import TestSerializer
from rest_framework import permissions, viewsets


class TestViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = LessonTest.objects.all()
    serializer_class = TestSerializer
    permission_classes = [permissions.DjangoModelPermissions]
