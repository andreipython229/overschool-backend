from rest_framework import permissions, viewsets

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from common_services.models import AudioFile
from common_services.serializers import AudioFileSerializer


class AudioFileViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    """
    Модель добавления аудиофайлов к занятиям
    """

    queryset = AudioFile.objects.all()
    serializer_class = AudioFileSerializer
    permission_classes = [permissions.DjangoModelPermissions]
