from common_services.mixins import WithHeadersViewSet, LoggingMixin
from courses.models import SchoolHeader
from courses.serializers import SchoolHeaderSerializer
from rest_framework import permissions, viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny

class SchoolHeaderViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = SchoolHeader.objects.all()
    serializer_class = SchoolHeaderSerializer
    permission_classes = (AllowAny,)