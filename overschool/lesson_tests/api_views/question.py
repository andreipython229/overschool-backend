from lesson_tests.models import Question
from lesson_tests.serializers import QuestionSerializer
from rest_framework import permissions, viewsets


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]
