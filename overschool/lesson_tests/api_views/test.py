from common_services.mixins import LoggingMixin, WithHeadersViewSet
from lesson_tests.models import SectionTest
from lesson_tests.serializers import TestSerializer
from rest_framework import permissions, viewsets


class TestViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = SectionTest.objects.all()
    serializer_class = TestSerializer
    permission_classes = [permissions.DjangoModelPermissions]
