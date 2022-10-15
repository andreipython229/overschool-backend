from common_services.mixins import LoggingMixin, WithHeadersViewSet
from schools.models import School
from schools.serializers import SchoolSerializer
from rest_framework import permissions, viewsets


class SchoolViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [permissions.DjangoModelPermissions]
