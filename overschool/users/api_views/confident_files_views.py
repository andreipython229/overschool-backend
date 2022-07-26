from rest_framework import viewsets

from .models import Documents
from .serializers import UploadSerializer


class ConfidentFilesViewSet(viewsets.ModelViewSet):
    queryset = Documents.objects.all()
    serializer_class = UploadSerializer
