from common_services.mixins import LoggingMixin, WithHeadersViewSet
from lesson_tests.models import Answer
from lesson_tests.serializers import AnswerSerializer
from rest_framework import permissions, viewsets


class AnswerViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [permissions.DjangoModelPermissions]
