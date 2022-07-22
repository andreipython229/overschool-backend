from rest_framework import permissions, viewsets

from lesson_tests.models import Answer
from lesson_tests.serializers import AnswerSerializer


class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [permissions.IsAuthenticated]
