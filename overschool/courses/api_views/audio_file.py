from common_services.mixins import WithHeadersViewSet
from courses.models import AudioFile
from courses.serializers import AudioFileSerializer
from rest_framework import permissions, viewsets


class AudioFileView(WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = AudioFile.objects.all()
    serializer_class = AudioFileSerializer
    permission_classes = [permissions.AllowAny]
