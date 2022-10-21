from rest_framework import permissions, viewsets

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Answer
from courses.serializers import AnswerSerializer


class AnswerViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [permissions.DjangoModelPermissions]
