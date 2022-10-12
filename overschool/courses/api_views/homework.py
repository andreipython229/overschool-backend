from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Homework
from courses.serializers import HomeworkSerializer
from rest_framework import permissions, viewsets


class HomeworkViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Homework.objects.all()
    serializer_class = HomeworkSerializer
    permission_classes = [permissions.DjangoModelPermissions]
