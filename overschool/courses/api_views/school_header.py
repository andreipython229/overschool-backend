from common_services.mixins import WithHeadersViewSet
from courses.models import SchoolHeader
from courses.serializers import SchoolHeaderSerializer
from rest_framework import permissions, viewsets


class SchoolHeaderViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = SchoolHeader.objects.all()
    serializer_class = SchoolHeaderSerializer
    permission_classes = [permissions.DjangoModelPermissions]