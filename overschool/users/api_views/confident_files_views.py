from rest_framework import viewsets

from users.models import Documents
from users.serializers import UploadSerializer


class ConfidentFilesViewSet(viewsets.ModelViewSet):
    queryset = Documents.objects.all()
    serializer_class = UploadSerializer

