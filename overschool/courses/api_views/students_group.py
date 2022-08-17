from common_services.mixins import WithHeadersViewSet
from courses.models import StudentsGroup
from courses.serializers import StudentsGroupSerializer
from rest_framework import permissions, viewsets


class StudentsGroupViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = StudentsGroup.objects.all()
    serializer_class = StudentsGroupSerializer
    permission_classes = [permissions.AllowAny]