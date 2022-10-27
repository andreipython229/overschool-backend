from django.core.exceptions import ObjectDoesNotExist
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Homework
from courses.serializers import HomeworkSerializer


class HomeworkViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Homework.objects.all()
    serializer_class = HomeworkSerializer
    permission_classes = [permissions.DjangoModelPermissions]


