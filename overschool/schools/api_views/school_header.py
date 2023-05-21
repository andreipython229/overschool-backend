from common_services.mixins import LoggingMixin, WithHeadersViewSet
from rest_framework import permissions, viewsets
from schools.models import SchoolHeader
from schools.serializers import SchoolHeaderSerializer


class SchoolHeaderViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = SchoolHeader.objects.all()
    serializer_class = SchoolHeaderSerializer
    permission_classes = [permissions.AllowAny]
