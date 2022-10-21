from rest_framework import permissions, viewsets

from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models import Question
from courses.serializers import QuestionSerializer


class QuestionViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.DjangoModelPermissions]
