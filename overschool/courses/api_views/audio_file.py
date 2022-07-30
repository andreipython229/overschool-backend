from courses.models import AudioFile
from courses.serializers import AudioFileSerializer
from rest_framework import mixins, permissions, viewsets
from users.permissions import IsEditor, IsStudent


class CreateAudioFileView(viewsets.GenericViewSet, mixins.CreateModelMixin):
    serializer_class = AudioFileSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsEditor | permissions.IsAdminUser,
    ]
    queryset = AudioFile.objects.all()


class GetAudioFileView(viewsets.GenericViewSet, mixins.CreateModelMixin):
    serializer_class = AudioFileSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsStudent,
        IsEditor | permissions.IsAdminUser,
    ]
    queryset = AudioFile.objects.all()
