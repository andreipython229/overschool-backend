from rest_framework import permissions, viewsets

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.models import TextFile
from common_services.serializers import TextFileSerializer


class TextFileViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """
    Модель добавления текстовых к занятиям
    """

    queryset = TextFile.objects.all()
    serializer_class = TextFileSerializer
    permission_classes = [permissions.DjangoModelPermissions]
