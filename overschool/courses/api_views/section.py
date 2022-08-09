from common_services.mixins import WithHeadersViewSet
from courses.models import Section
from courses.serializers import SectionSerializer
from rest_framework import permissions, viewsets
from users.permissions import IsEditor


class SectionViewSet(WithHeadersViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [permissions.IsAuthenticated, IsEditor | permissions.IsAdminUser]
