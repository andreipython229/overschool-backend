from common_services.mixins import WithHeadersViewSet
from courses.models import CourseHeader
from courses.serializers import CourseHeaderSerializer
from rest_framework import permissions, viewsets


class CourseHeaderViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = CourseHeader.objects.all()
    serializer_class = CourseHeaderSerializer
    permission_classes = [permissions.DjangoModelPermissions]
