from rest_framework import viewsets

from users.models import Documents
from users.serializers import UploadSerializer


class ConfidentFilesViewSet(viewsets.ModelViewSet):
    """Эндпоинт для загрузкт документов\n
    Эндпоинт для загрузкт документов"""
    queryset = Documents.objects.all()
    serializer_class = UploadSerializer
