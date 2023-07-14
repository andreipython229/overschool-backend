from common_services.apply_swagger_auto_schema import apply_swagger_auto_schema
from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser
from users.models import Documents
from users.serializers import UploadSerializer


class ConfidentFilesViewSet(viewsets.ModelViewSet):
    """Эндпоинт для загрузкт документов\n
    Эндпоинт для загрузкт документов"""

    queryset = Documents.objects.all()
    serializer_class = UploadSerializer

    parser_classes = (MultiPartParser,)


ConfidentFilesViewSet = apply_swagger_auto_schema(tags=["upload"])(
    ConfidentFilesViewSet
)
