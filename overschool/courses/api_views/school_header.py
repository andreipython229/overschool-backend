from rest_framework import permissions, viewsets

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import SchoolHeader
from courses.serializers import SchoolHeaderSerializer


class SchoolHeaderViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = SchoolHeader.objects.all()
    serializer_class = SchoolHeaderSerializer
    permission_classes = [permissions.DjangoModelPermissions]
