# -*- coding: utf-8 -*-
from rest_framework import permissions, viewsets


from lesson_tests.serializers import (AnswerSerializer, QuestionSerializer,
                               TestSerializer)
from rest_framework import viewsets
from lesson_tests.models import Answer, LessonTest, Question


class TestViewSet(viewsets.ModelViewSet):
    queryset = LessonTest.objects.all()
    serializer_class = TestSerializer
    permission_classes = [permissions.IsAuthenticated]


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]


class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [permissions.IsAuthenticated]


