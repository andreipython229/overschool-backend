from courses.models import AudioFile
from courses.serializers import AudioFileSerializer
from rest_framework import viewsets
from rest_framework.permissions import AllowAny


class AudioFileView(viewsets.ModelViewSet):
    serializer_class = AudioFileSerializer
    permission_classes = [AllowAny]
    queryset = AudioFile.objects.all()
